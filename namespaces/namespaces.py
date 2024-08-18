from typing import Optional

import pulumi_kubernetes as k8s
from pulumi import ComponentResource, ResourceOptions


class Namespace(ComponentResource):
    def __init__(
        self,
        name: str,
        random_id: bool = True,
        opts: Optional[ResourceOptions] = None,
    ) -> None:
        super().__init__("notdodo:k8s:Namespace", f"{name}-namespace", None, opts)
        if not random_id:
            ns = k8s.core.v1.Namespace(
                name,
                opts,
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    labels={
                        "kubernetes.io/metadata.name": name,
                    },
                    name=name,
                ),
                spec=k8s.core.v1.NamespaceSpecArgs(
                    finalizers=["kubernetes"],
                ),
            )
        else:
            ns = k8s.core.v1.Namespace(
                name,
                None,
                opts,
                # api_version="v1",
                # kind="Namespace",
                # metadata=None,
                # spec=None,
            )
        self.name = ns.metadata["name"]


class Namespaces:
    __DEFAULT_NAMESPACES = [
        "default",
        "kube-node-lease",
        "kube-public",
        "kube-system",
        "local-path-storage",
    ]
    __namespaces: dict[str, Namespace] = {}

    def __init__(self) -> None:
        for namespace in self.__DEFAULT_NAMESPACES:
            self.__import_default_ns(namespace)

    def create(
        self,
        name: str,
        random_id: bool = True,
        opts: Optional[ResourceOptions] = None,
    ) -> Namespace:
        namespace = Namespace(name, random_id, opts=opts)
        self.__namespaces[name] = namespace
        return namespace

    def get(self, name: str) -> Namespace:
        return self.__namespaces[name]

    def import_ns(
        self,
        name: str,
        opts: Optional[ResourceOptions] = None,
    ) -> Namespace:
        namespace = Namespace(name, False, opts=opts)
        self.__namespaces[name] = namespace
        return namespace

    def __import_default_ns(self, name: str) -> None:
        self.import_ns(
            name,
            opts=ResourceOptions(import_=name, retain_on_delete=True),
        )

    # def annotate(self, namespace: str, name: str) -> None:
    #     k8s.core.v1.Namespace(
    #         name,
    #         # args=k8s.core.v1.NamespaceInitArgs(
    #         #     metadata=k8s.meta.v1.ObjectMetaArgs(
    #         #         annotations={
    #         #             "linkerd.io/inject": "enabled",
    #         #             "pulumi.com/patchForce": "true",
    #         #         },
    #         #         name=namespace,
    #         #     ),
    #         # ),
    #         opts=ResourceOptions(provider=provider),
    #     )
