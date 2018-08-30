import random
import flask


class Handler:
    def __init__(self, cls):
        self.cls = cls
        self.instances = {}

    def new(self):
        eh = EventHandler()
        i = self.cls(event_handler=eh)
        self.instances[id(i)] = (i, eh)
        return str(id(i))

    def invoke(self, instance, method, args):
        m = getattr(self.instances[instance][0], method)
        if callable(m):
            return m(**args)

    def new_player(self, instance):
        i, eh = self.instances[instance]
        pid = eh.new_player()
        try:
            i.new_player(pid)
        except Exception:
            pass
        return pid

    def player_events(self, instance, pid):
        return self.instances[instance][1].player_events(pid)

    def ack_event(self, instance, pid, event):
        self.instances[instance][1].ack_event(pid, event)


class EventHandler:
    def __init__(self):
        self.events = {}

    def new_player(self):
        for i in range(1000):
            pid = random.randrange(8999) + 1000
            if pid not in self.events:
                self.events[pid] = (0, {})
                return pid
        raise KeyError()

    def player_events(self, pid):
        return self.events[pid][1]

    def ack_event(self, pid, n):
        del self.events[pid][1][n]

    def post_event(self, pid, event):
        n, events = self.events[pid]
        n += 1
        events[n] = event
        self.events[pid] = (n, events)


class Server:
    def __init__(self):
        self.handlers = {}
        app = self.app = flask.Flask('remoter')
        app.route('/<cls>', methods=['POST'])(self.new)
        app.route('/<cls>/<int:instance>/<method>', methods=['POST'])(self.invoke)
        app.route('/<cls>/<int:instance>/player', methods=['POST'])(self.new_player)
        app.route('/<cls>/<int:instance>/player/<int:pid>', methods=['GET'])(self.player_events)
        app.route('/<cls>/<int:instance>/player/<int:pid>/<int:event>', methods=['POST'])(self.ack_player_event)

    def run(self, host=None, port=None, debug=False):
        self.app.run(host=host, port=port, debug=debug)

    def register(self, cls):
        self.handlers[cls.__module__ + '.' + cls.__name__] = Handler(cls)

    # POST /<cls>
    def new(self, cls):
        return self.handlers[cls].new()

    # POST /<cls>/<instance>/<method> {"arg1": "value1", ...}
    def invoke(self, cls, instance, method):
        print("invoke", cls, instance, method)
        args = flask.request.get_json(force=True)
        return flask.jsonify(self.handlers[cls].invoke(instance, method, args))

    # POST /<cls>/<instance>/player
    def new_player(self, cls, instance):
        return flask.jsonify(self.handlers[cls].new_player(instance))

    # GET /<cls>/<instance>/player/<pid>
    def player_events(self, cls, instance, pid):
        return flask.jsonify(self.handlers[cls].player_events(instance, pid))

    # POST /<cls>/<instance>/player/<pid>/<event>
    def ack_player_event(self, cls, instance, pid, event):
        self.handlers[cls].ack_event(instance, pid, event)
        return ""
