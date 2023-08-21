import pulumi
import pulumi_kubernetes as k8s

from provider import provider


def create_native_sg(ns: str):
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


def create_openebs_sg(ns: str):
    openebs = k8s.helm.v3.Release(
        "openebs",
        k8s.helm.v3.ReleaseArgs(
            chart="openebs",
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://openebs.github.io/charts",
            ),
            version="3.8.0",
            namespace=ns,
            wait_for_jobs=True,
            values={
                "ndm": {"enabled": False},
                "ndmOperator": {"enabled": False},
                "localprovisioner": {"enableDeviceClass": False},
            },
        ),
        opts=pulumi.ResourceOptions(provider=provider),
    )
    # Patch the storage class the make it the default
    storage_class = k8s.storage.v1.StorageClass(
        "openebs-hostpath",
        provisioner="openebs.io/local",
        volume_binding_mode="WaitForFirstConsumer",
        reclaim_policy="Delete",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="openebs-hostpath",
            annotations={
                "storageclass.kubernetes.io/is-default-class": "true",
            },
            namespace=ns,
        ),
        opts=pulumi.ResourceOptions(provider=provider, depends_on=openebs),
    )
    return storage_class, "openebs-hostpath"


def init(ns: str, storage_class_type: str = "native"):
    return (
        create_native_sg(ns)
        if storage_class_type == "native"
        else create_openebs_sg(ns)
    )
