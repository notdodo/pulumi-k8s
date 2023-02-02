import pulumi_kubernetes as k8s
from pulumi_command import local
import pulumi

CONFIG = """
disable_mlock = true
ui = true
listener "tcp" {
  tls_disable = 1
  address = "[::]:8200"
  cluster_address = "[::]:8201"
}
storage "file" {
  path = "/vault/data"
}

"""
# service_registration "kubernetes" {}


def init_vault(namespace: str = "vault", deps: list = []):
    vault = k8s.helm.v3.Release(
        "vault",
        k8s.helm.v3.ReleaseArgs(
            chart="vault",
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://helm.releases.hashicorp.com/",
            ),
            namespace=namespace,
            wait_for_jobs=True,
            replace=True,
            recreate_pods=True,
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
                    "annotations": {
                        "linkerd.io/inject": "enabled",
                    },
                    "standalone": {
                        "config": CONFIG,
                    },
                },
                "service": {
                    "annotations": {
                        "linkerd.io/inject": "enabled",
                    },
                },
                "certs": {
                    "annotations": {
                        "linkerd.io/inject": "enabled",
                    },
                },
            },
        ),
        opts=pulumi.ResourceOptions(depends_on=deps),
    )
    srv = vault.resource_names["Service/v1"][0]

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
        opts=pulumi.ResourceOptions(parent=out, depends_on=out),
    )
    pulumi.export("vault_root_token", out.stdout)

    return srv
