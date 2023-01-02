import pulumi_kubernetes as k8s


class PersistentVolume:
    def __init__(
        self, name: str, namespace: str, size: str, storageclass: str = "default"
    ):
        k8s.core.v1.PersistentVolume(
            name,
            metadata=k8s.meta.v1.ObjectMetaArgs(name=name, namespace=namespace),
            spec=k8s.core.v1.PersistentVolumeSpecArgs(
                capacity={"storage": size},
                access_modes=["ReadWriteOnce"],
                persistent_volume_reclaim_policy="Retain",
                storage_class_name=storageclass,
                local=k8s.core.v1.LocalVolumeSourceArgs(path="dev/sda2"),
                node_affinity=k8s.core.v1.VolumeNodeAffinityArgs(
                    required=k8s.core.v1.NodeSelectorArgs(
                        node_selector_terms=[
                            k8s.core.v1.NodeSelectorTermArgs(
                                match_expressions=[
                                    k8s.core.v1.NodeSelectorRequirementArgs(
                                        key="kubernetes.io/hostname",
                                        operator="In",
                                        values=["k8sfreenode"],
                                    )
                                ]
                            )
                        ]
                    )
                ),
            ),
        )
