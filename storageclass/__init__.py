import pulumi_kubernetes as k8s
import pulumi


def init():
    storage_class = k8s.storage.v1.StorageClass(
        "default",
        provisioner="kubernetes.io/no-provisioner",
        volume_binding_mode="Immediate",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="default",
            annotations={"storageclass.kubernetes.io/is-default-class": "true"},
        ),
    )
    pulumi.export("storage_class_name", storage_class.metadata.name)
