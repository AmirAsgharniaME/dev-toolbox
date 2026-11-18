#!/usr/bin/env python3
"""Persistent GTK front end for the Bash picker's menu requests."""
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import threading


def menu_client(arguments):
    request = {'arguments': arguments, 'items': sys.stdin.read().splitlines(),
               'generation': os.environ['PICKER_GENERATION']}
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(os.environ['PICKER_SOCKET'])
        stream = client.makefile('rwb')
        stream.write((json.dumps(request) + '\n').encode())
        stream.flush()
        response = stream.readline()
        if not response:
            return 1
        reply = json.loads(response)
    if reply.get('cancel'):
        return 1
    print(reply['value'])
    return 0


class History:
    """Menu stages and committed choices; later stages depend on earlier choices."""
    def __init__(self):
        self.steps = []

    def prepare(self, index, request):
        signature = (request['arguments'], request['items'])
        if index < len(self.steps) and self.steps[index]['signature'] != signature:
            del self.steps[index:]
        if index == len(self.steps):
            self.steps.append({'signature': signature, 'value': None})
        return self.steps[index]

    def choose(self, index, request, value):
        step = self.prepare(index, request)
        if step['value'] != value:
            del self.steps[index + 1:]
            step['value'] = value


def menu_reply_value(request, value):
    """Turn stored multi-row indices back into the shell menu's line format."""
    if isinstance(value, list):
        return '\n'.join(request['items'][row] for row in value)
    return value


def matches_filter(item, text, fuzzy=False):
    item, text = item.casefold(), text.casefold()
    if not fuzzy:
        return text in item
    for word in text.split():
        remaining = iter(item)
        if not all(any(char == candidate for candidate in remaining) for char in word):
            return False
    return True


def wrapped_index(index, count, direction):
    """Return the next visible-row index, wrapping within ``count`` rows."""
    if count <= 0:
        return None
    if count == 1:
        return 0
    return (index + direction) % count


class MultiSelection:
    """A stable selection of original menu rows, independent of filtering."""
    def __init__(self, items, selected=None, minimum=1, maximum=None):
        self.items = list(items)
        self.selected = set(selected or [])
        self.minimum = minimum
        self.maximum = maximum

    def toggle(self, index):
        if index in self.selected:
            self.selected.remove(index)
        else:
            self.selected.add(index)

    def visible(self, text='', fuzzy=False):
        return [(index, item) for index, item in enumerate(self.items)
                if matches_filter(item, text, fuzzy)]

    def values(self):
        return [item for index, item in enumerate(self.items) if index in self.selected]

    def display(self, index):
        marker = '✓  ' if index in self.selected else '□  '
        return marker + self.items[index]

    def validation_error(self):
        count = len(self.selected)
        if count < self.minimum:
            return f"Select at least {self.minimum} file{'s' if self.minimum != 1 else ''}."
        if self.maximum is not None and count > self.maximum:
            return f"Select no more than {self.maximum} file{'s' if self.maximum != 1 else ''}."
        return None


def run_window(script):
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    from gi.repository import Gdk, GLib, Gtk

    class PickerWindow(Gtk.Window):
        def __init__(self):
            super().__init__(title='Prompt Picker')
            self.set_default_size(760, 500)
            self.set_position(Gtk.WindowPosition.CENTER)
            self.set_type_hint(Gdk.WindowTypeHint.NORMAL)
            self.connect('delete-event', self.close_window)
            self.connect('key-press-event', self.key_pressed)
            self.history = History()
            self.current = -1
            self.target = 0
            self.generation = 0
            self.pending = None
            self.process = None
            self.closing = False
            self.tempdir = tempfile.TemporaryDirectory(prefix='prompt-picker-')
            self.socket_path = os.path.join(self.tempdir.name, 'menu.sock')
            self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.server.bind(self.socket_path)
            self.server.listen(4)
            self.server.settimeout(0.2)
            self.requests = 0

            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            box.set_border_width(12)
            self.add(box)
            self.label = Gtk.Label(xalign=0)
            box.pack_start(self.label, False, False, 0)
            self.selection_label = Gtk.Label(xalign=0)
            self.selection_label.set_line_wrap(True)
            box.pack_start(self.selection_label, False, False, 0)
            self.entry = Gtk.Entry()
            self.entry.set_placeholder_text('Type to filter; Ctrl+B / Ctrl+F move the text cursor')
            self.entry.connect('key-press-event', self.key_pressed)
            self.entry.connect('changed', self.filter_changed)
            box.pack_start(self.entry, False, False, 0)
            self.model = Gtk.ListStore(str, int)
            self.view = Gtk.TreeView(model=self.model)
            self.view.set_headers_visible(False)
            self.view.append_column(Gtk.TreeViewColumn('', Gtk.CellRendererText(), text=0))
            self.view.connect('key-press-event', self.key_pressed)
            self.view.connect('row-activated', self.row_activated)
            scroller = Gtk.ScrolledWindow()
            scroller.add(self.view)
            box.pack_start(scroller, True, True, 0)
            buttons = Gtk.ButtonBox()
            buttons.set_layout(Gtk.ButtonBoxStyle.END)
            self.back_button = Gtk.Button(label='Back')
            self.back_button.connect('clicked', lambda *_: self.back())
            self.forward_button = Gtk.Button(label='Forward')
            self.forward_button.connect('clicked', lambda *_: self.forward())
            cancel = Gtk.Button(label='Cancel')
            cancel.connect('clicked', self.close_window)
            self.toggle_button = Gtk.Button(label='Toggle file')
            self.toggle_button.connect('clicked', lambda *_: self.toggle_current())
            self.done_button = Gtk.Button(label='Select')
            self.done_button.connect('clicked', lambda *_: self.accept())
            for button in (self.back_button, self.forward_button, cancel,
                           self.toggle_button, self.done_button):
                buttons.add(button)
            box.pack_start(buttons, False, False, 0)
            threading.Thread(target=self.serve, daemon=True).start()
            self.show_all()
            self.entry.grab_focus()
            self.start_worker(0)

        def start_worker(self, target):
            self.stop_worker()
            self.generation += 1
            self.target = target
            self.requests = 0
            self.pending = None
            environment = os.environ.copy()
            environment.update(PICKER_WORKER='1', PICKER_SOCKET=self.socket_path,
                               PICKER_GENERATION=str(self.generation))
            self.process = subprocess.Popen(['bash', script], env=environment,
                                            start_new_session=True)
            generation, process = self.generation, self.process
            threading.Thread(target=self.watch_worker, args=(generation, process), daemon=True).start()

        def watch_worker(self, generation, process):
            process.wait()
            GLib.idle_add(self.worker_finished, generation)

        def worker_finished(self, generation):
            if generation == self.generation and not self.closing:
                self.close_window()
            return False

        def stop_worker(self):
            if self.pending:
                try:
                    self.pending.close()
                except OSError:
                    pass
                self.pending = None
            if self.process and self.process.poll() is None:
                try:
                    os.killpg(self.process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass

        def serve(self):
            while not self.closing:
                try:
                    conn, _ = self.server.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break
                threading.Thread(target=self.receive, args=(conn,), daemon=True).start()

        def receive(self, conn):
            try:
                with conn.makefile('rb') as stream:
                    line = stream.readline()
                request = json.loads(line)
                GLib.idle_add(self.receive_menu, conn, request)
            except (OSError, ValueError):
                conn.close()

        def reply(self, conn, value):
            try:
                conn.sendall((json.dumps({'value': value}) + '\n').encode())
            except OSError:
                pass
            conn.close()

        def receive_menu(self, conn, request):
            if self.closing or request['generation'] != str(self.generation):
                conn.close()
                return False
            index = self.requests
            self.requests += 1
            previous = self.history.prepare(index, request)
            if index < self.target:
                if previous['value'] is None:
                    conn.close()
                    self.close_window()
                else:
                    self.reply(conn, menu_reply_value(request, previous['value']))
                return False
            self.current = index
            self.pending = conn
            self.request = request
            args = request['arguments']
            self.title = args[args.index('-p') + 1] if '-p' in args else 'Select:'
            if os.environ.get('PICKER_DEBUG'):
                print('MENU', index, self.title, request['items'], file=sys.stderr, flush=True)
            self.by_index = '-format' in args and args[args.index('-format') + 1] == 'i'
            self.multi = '-multi-select' in args
            self.group_info = args[args.index('-group') + 1] if '-group' in args else ''
            self.final_summary = args[args.index('-summary') + 1] if '-summary' in args else ''
            self.custom = '-no-custom' not in args
            self.fuzzy = '-matching' in args and args[args.index('-matching') + 1] == 'fuzzy'
            self.label.set_text(self.title)
            if self.final_summary:
                self.selection_label.set_text('Selections: ' + self.final_summary)
            prior_value = previous['value']
            self.multi_selection = MultiSelection(request['items'], prior_value or []) if self.multi else None
            custom_value = prior_value if self.custom and prior_value not in request['items'] else ''
            self.entry.set_text('' if self.multi else (custom_value or ''))
            self.populate(prior_value)
            self.update_selection_summary()
            self.update_buttons()
            self.entry.grab_focus()
            return False

        def populate(self, preferred=None):
            if preferred is None:
                model, row = self.view.get_selection().get_selected()
                if row is not None:
                    preferred = (str(model[row][1]) if self.by_index
                                 else model[row][0])
            text = self.entry.get_text().casefold()
            self.model.clear()
            match_row = None
            for index, item in enumerate(self.request['items']):
                if not matches_filter(item, text, self.fuzzy):
                    continue
                display = self.multi_selection.display(index) if self.multi else item
                row = self.model.append([display, index])
                value = str(index) if self.by_index else item
                if preferred == value:
                    match_row = row
            selection = self.view.get_selection()
            if match_row is not None:
                selection.select_iter(match_row)
            elif len(self.model):
                selection.select_path(Gtk.TreePath.new_from_indices([0]))

        def filter_changed(self, _entry):
            if hasattr(self, 'request') and self.pending:
                self.populate()

        def selected_value(self):
            model, row = self.view.get_selection().get_selected()
            if row is not None:
                return str(model[row][1]) if self.by_index else model[row][0]
            if self.custom and self.entry.get_text().strip():
                return self.entry.get_text()
            return None

        def toggle_current(self):
            if not self.pending or not self.multi:
                return
            model, row = self.view.get_selection().get_selected()
            if row is None:
                return
            self.multi_selection.toggle(int(model[row][1]))
            self.populate()
            self.update_selection_summary()

        def row_activated(self, _view, _path, _column):
            if self.multi:
                self.toggle_current()
            else:
                self.accept()

        def update_selection_summary(self):
            if not getattr(self, 'multi', False):
                self.selection_label.set_text(('Selections: ' + self.final_summary)
                                               if self.final_summary else '')
                self.done_button.set_label('Select')
                self.done_button.set_sensitive(True)
                return
            values = self.multi_selection.values()
            prefix = (self.group_info + ' — ') if self.group_info else ''
            summary = ', '.join(values) if values else 'none'
            if len(summary) > 180:
                summary = summary[:177] + '…'
            error = self.multi_selection.validation_error()
            self.selection_label.set_text(
                f'{prefix}Selected: {len(values)} file' + ('s' if len(values) != 1 else '') +
                f' — {summary}' + (f' — {error}' if error else ''))
            self.done_button.set_label('Done')
            self.done_button.set_sensitive(error is None)

        def accept(self):
            if not self.pending:
                return
            if self.multi:
                error = self.multi_selection.validation_error()
                if error:
                    self.selection_label.set_text(self.selection_label.get_text() + ' — ' + error)
                    return
                value = self.multi_selection.values()
                self.history.choose(self.current, self.request,
                                    sorted(self.multi_selection.selected))
                conn, self.pending = self.pending, None
                self.reply(conn, '\n'.join(value))
                return
            value = self.selected_value()
            if value is None:
                return
            self.history.choose(self.current, self.request, value)
            conn, self.pending = self.pending, None
            self.reply(conn, value)

        def back(self):
            if self.pending and self.current > 0:
                self.start_worker(self.current - 1)

        def forward(self):
            if not self.pending or self.title == 'Generate prompt:':
                return
            # Moving forward can choose the highlighted item, but final output
            # always requires a separate explicit confirmation.
            if not self.multi:
                self.accept()

        def update_buttons(self):
            self.back_button.set_sensitive(self.current > 0)
            self.forward_button.set_sensitive(self.current + 1 < len(self.history.steps))

        def key_pressed(self, _widget, event):
            if event.state & Gdk.ModifierType.CONTROL_MASK and self.entry.has_focus():
                if event.keyval in (Gdk.KEY_b, Gdk.KEY_f):
                    offset = -1 if event.keyval == Gdk.KEY_b else 1
                    position = max(0, self.entry.get_position() + offset)
                    self.entry.set_position(position)
                    return True
            if event.state & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK):
                return False
            if event.keyval == Gdk.KEY_Left:
                self.back(); return True
            if event.keyval == Gdk.KEY_Right:
                self.forward(); return True
            if event.keyval == Gdk.KEY_Escape:
                self.close_window(); return True
            if event.keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
                if self.multi:
                    self.toggle_current()
                else:
                    self.accept()
                return True
            if event.keyval in (Gdk.KEY_Up, Gdk.KEY_Down):
                model, row = self.view.get_selection().get_selected()
                if len(model):
                    index = model.get_path(row).get_indices()[0] if row else 0
                    direction = 1 if event.keyval == Gdk.KEY_Down else -1
                    index = wrapped_index(index, len(model), direction)
                    path = Gtk.TreePath.new_from_indices([index])
                    self.view.get_selection().select_path(path)
                    self.view.scroll_to_cell(path, None, False, 0, 0)
                return True
            return False

        def close_window(self, *_args):
            if not self.closing:
                self.closing = True
                self.stop_worker()
                self.server.close()
                self.tempdir.cleanup()
                self.destroy()
                Gtk.main_quit()
            return False

    PickerWindow()
    Gtk.main()


if __name__ == '__main__':
    if sys.argv[1] == '--menu':
        sys.exit(menu_client(sys.argv[2:]))
    run_window(sys.argv[1])
