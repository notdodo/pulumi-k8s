import pulumi_kubernetes as k8s
from pulumi import ResourceOptions


class Namespace(k8s.core.v1.Namespace):
    def __init__(self, name: str, fixed_name: bool = False, args=None, opts=None):
        if fixed_name:
            ns_init = k8s.core.v1.NamespaceInitArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(name=name),
            )
            args = ns_init

        # if args is None:
        #     args = k8s.core.v1.NamespaceInitArgs(
        #         metadata=k8s.meta.v1.ObjectMetaArgs(
        #             annotations={"linkerd.io/inject": "enabled"}
        #         ),
        #     )

        namespace = k8s.core.v1.Namespace(
            name,
            args,
            opts,
        )
        self.__metadata = namespace.metadata
        self.name = self.__metadata["name"]


class Namespaces:
    __DEFAULT_NAMESPACES = ["default", "kube-node-lease", "kube-public", "kube-system"]
    __namespaces = {}

    def __init__(self) -> None:
        for namespace in self.__DEFAULT_NAMESPACES:
            self.__import_default_ns(namespace)

    def create_ns(self, name, fixed_name: bool = False, args=None, opts=None):
        namespace = Namespace(name, fixed_name, args, opts=opts)
        self.__namespaces[name] = namespace
        return namespace

    def create_namespaces(self, namespaces: list):
        for ns in namespaces:
            if len(ns) == 2:
                self.create_ns(ns[0], fixed_name=ns[1])
            else:
                self.create_ns(ns, fixed_name=False)

    def get_ns(self, name):
        return self.__namespaces[name]

    def import_ns(self, name, args=None, opts=None):
        namespace = Namespace(name, True, args, opts=opts)
        self.__namespaces[name] = namespace
        return namespace

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
            opts=ResourceOptions(import_=name, retain_on_delete=True),
        )
