from typing import Tuple

import pulumi
import pulumi_kubernetes as k8s

from provider import provider


def create_native_sg(ns: str) -> Tuple[k8s.storage.v1.StorageClass, str]:
    storage_class = k8s.storage.v1.StorageClass(
        "default",
        provisioner="kubernetes.io/no-provisioner",
        volume_binding_mode="Immediate",
        reclaim_policy="Delete",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="default",
            annotations={"storageclass.kubernetes.io/is-default-class": "true"},
            namespace=ns,
        ),
    )
    return storage_class, "default"


def create_openebs_sg(ns: str) -> Tuple[k8s.helm.v3.Release, str]:
    openebs = k8s.helm.v3.Release(
        "openebs",
        k8s.helm.v3.ReleaseArgs(
            chart="openebs",
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://openebs.github.io/openebs",
            ),
            version="4.1.0",
            namespace=ns,
            wait_for_jobs=True,
            values={
                "ndm": {"enabled": False},
                "ndmOperator": {"enabled": False},
                "localprovisioner": {
                    "enableDeviceClass": False,
                    "hostpathClass": {
                        "isDefaultClass": True,
                    },
                },
            },
        ),
        opts=pulumi.ResourceOptions(provider=provider),
    )
    return openebs, "openebs-hostpath"


def init(
    ns: str, storage_class_type: str = "native"
) -> Tuple[pulumi.CustomResource, str]:
    return (
        create_native_sg(ns)
        if storage_class_type == "native"
        else create_openebs_sg(ns)
    )
