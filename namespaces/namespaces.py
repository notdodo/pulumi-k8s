import pulumi_kubernetes as k8s
from pulumi import ResourceOptions


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

    def __init__(self) -> None:
        pass
        self.__import_default_ns("default")
        self.__import_default_ns("kube-node-lease")
        self.__import_default_ns("kube-public")
        self.__import_default_ns("kube-system")

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

    def __import_default_ns(self, name):
        self.import_ns(
            name,
            k8s.core.v1.NamespaceInitArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    name=name,
                    labels={"kubernetes.io/metadata.name": name},
                ),
                spec=k8s.core.v1.NamespaceSpecArgs(finalizers=["kubernetes"]),
            ),
            opts=ResourceOptions(import_=name),
        )
