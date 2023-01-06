# pyright: reportShadowedImports=false
import pulumi_kubernetes as k8s
from pulumi_command import local
import pulumi
from namespaces import namespaces
from pvs import persistentvolumes
from cni import cilium
import csr
import metrics
import storageclass

storageclass.init()

nss = namespaces.Namespaces()
kubesystem_ns = nss.get_ns("kube-system")
csr.auto_csr_approver(kubesystem_ns.name)
metrics.init_metrics_server(kubesystem_ns.name)

cilium_ns = nss.create_ns("cilium-system")
cilium_dpl = cilium.init_cilium(cilium_ns.name)

vault_ns = nss.create_ns("vault")
persistentvolumes.PersistentVolume("vault-pv-datastorage", vault_ns.name, "500M")
persistentvolumes.PersistentVolume("vault-pv-auditstorage", vault_ns.name, "500M")

vault = k8s.helm.v3.Release(
    "vault",
    k8s.helm.v3.ReleaseArgs(
        chart="vault",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://helm.releases.hashicorp.com/",
        ),
        namespace=vault_ns.name,
        # https://github.com/hashicorp/vault-helm/blob/main/values.yaml
        values={
            "server": {
                # https://github.com/hashicorp/vault-helm/issues/826
                # "volumes": [
                #     {
                #         "name": "data",
                #         "persistentVolumeClaim": {"claimName": vault_data_pvc},
                #     },
                #     {
                #         "name": "audit",
                #         "persistentVolumeClaim": {"claimName": vault_audit_pvc},
                #     },
                # ],
                # "volumeMounts": [
                #     {"mountPath": "/vault/data", "name": "data"},
                #     {"mountPath": "/vault/audit", "name": "audit"},
                # ],
                "dataStorage": {
                    "enabled": True,
                    "size": "500M",
                },
                "auditStorage": {
                    "enabled": True,
                    "size": "500M",
                },
            },
        },
    ),
    opts=pulumi.ResourceOptions(depends_on=cilium_dpl),
)


out = local.Command(
    "unseal-vault",
    create="./vault-utils/unseal.sh",
    opts=pulumi.ResourceOptions(parent=vault, depends_on=vault),
)

k8s.core.v1.Secret(
    "vault-root-token",  # To avoid losing access: TODO
    metadata=k8s.meta.v1.ObjectMetaArgs(namespace=vault_ns.name),
    immutable=True,
    string_data={"root-token": out.stdout},
)

pulumi.export("vault_root_token", out.stdout)

# vault_data_pvc = k8s.core.v1.PersistentVolumeClaim(
#     "data-vault",
#     metadata=k8s.meta.v1.ObjectMetaArgs(
#         namespace=vault_ns.name,
#         labels={"app.kubernetes.io/name": "vault", "component": "server"},
#     ),
#     spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
#         access_modes=["ReadWriteOnce"],
#         resources=k8s.core.v1.ResourceRequirementsArgs(
#             requests={"storage": "500M"},
#         ),
#     ),
# )

# vault_audit_pvc = k8s.core.v1.PersistentVolumeClaim(
#     "audit-vault",
#     metadata=k8s.meta.v1.ObjectMetaArgs(
#         namespace=vault_ns.name,
#         labels={"app.kubernetes.io/name": "vault", "component": "server"},
#     ),
#     spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
#         access_modes=["ReadWriteOnce"],
#         resources=k8s.core.v1.ResourceRequirementsArgs(
#             requests={"storage": "500M"},
#         ),
#     ),
# )
