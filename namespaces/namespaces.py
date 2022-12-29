import pulumi_kubernetes as k8s


class Namespaces:
    __namespaces = {
        "kube-system": "",
    }

    def __init(self):
        pass

    def create_ns(self, name):
        ns = Namespace(name)
        self.__namespaces[name] = ns
        return ns

    def get_ns(self, name):
        return self.__namespaces[name]


class Namespace:
    def __init__(self, name: str):
        ns = k8s.core.v1.Namespace(name)
        self.metadata = ns.metadata
        self.name = self.metadata["name"]
