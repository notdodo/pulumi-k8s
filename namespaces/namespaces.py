import pulumi_kubernetes as k8s
import pulumi


class Namespace(k8s.core.v1.Namespace):
    def __init__(self, name: str, fixed_name: bool = False, args=None, opts=None):
        if fixed_name and args is None:
            ns_init = k8s.core.v1.NamespaceInitArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(name=name)
            )
            args = ns_init

        ns = k8s.core.v1.Namespace(name, args, opts)
        self.__metadata = ns.metadata
        self.name = self.__metadata.name


class Namespaces:
    __namespaces = {}

    def create_ns(self, name, fixed_name: bool = False, args=None, opts=None):
        ns = Namespace(name, fixed_name, args, opts=opts)
        self.__namespaces[name] = ns
        return ns

    def get_ns(self, name):
        return self.__namespaces[name]

    def import_ns(self, name, args=None, opts=None):
        ns = Namespace(name, True, args, opts=opts)
        self.__namespaces[name] = ns
        return ns
