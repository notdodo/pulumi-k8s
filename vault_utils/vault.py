import pulumi_kubernetes as k8s
from pulumi_command import local
import pulumi


def init_vault(
    namespace: str = "vault", storage_class: str = "default", deps: list = []
):
    vault = k8s.helm.v3.Release(
        "vault",
        k8s.helm.v3.ReleaseArgs(
            chart="vault",
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://helm.releases.hashicorp.com/",
            ),
            namespace=namespace,
            wait_for_jobs=True,
            # https://github.com/hashicorp/vault-helm/blob/main/values.yaml
            values={
                "server": {
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
        opts=pulumi.ResourceOptions(depends_on=deps),
    )

    out = local.Command(
        "unseal-vault",
        create="./vault_utils/unseal.sh",
        opts=pulumi.ResourceOptions(parent=vault, depends_on=vault),
    )

    k8s.core.v1.Secret(
        "vault-root-token",  # To avoid losing access: TODO remove in prod
        metadata=k8s.meta.v1.ObjectMetaArgs(namespace=namespace),
        immutable=True,
        string_data={"root-token": out.stdout},
        opts=pulumi.ResourceOptions(parent=vault, depends_on=[out, vault]),
    )
    pulumi.export("vault_root_token", out.stdout)
