import pulumi_kubernetes as k8s
from pulumi import ResourceOptions

from provider import provider


class Namespace(k8s.core.v1.Namespace):
    def __init__(self, name: str, random_id: bool = True, args=None, opts=None):
        if not random_id and args is None:
            args = k8s.core.v1.NamespaceInitArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(name=name)
            )

        self.__metadata = k8s.core.v1.Namespace(name, args, opts).metadata
        self.name = self.__metadata["name"]


class Namespaces:
    __DEFAULT_NAMESPACES = [
        "default",
        "kube-node-lease",
        "kube-public",
        "kube-system",
    ]
    __namespaces = {}

    def __init__(self) -> None:
        for namespace in self.__DEFAULT_NAMESPACES:
            self.__import_default_ns(namespace)

    def create(self, name, random_id: bool = True, args=None, opts=None):
        namespace = Namespace(name, random_id, args, opts=opts)
        self.__namespaces[name] = namespace
        return namespace

    def create_namespaces(self, namespaces: list[dict]):
        for ns in namespaces:
            self.create(ns.get("name"), ns.get("generate_id", True))

    def get(self, name):
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

    def annotate(self, namespace, name):
        k8s.core.v1.Namespace(
            name,
            args=k8s.core.v1.NamespaceInitArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    annotations={
                        "linkerd.io/inject": "enabled",
                        "pulumi.com/patchForce": "true",
                    },
                    name=namespace,
                ),
            ),
            opts=ResourceOptions(provider=provider),
        )
