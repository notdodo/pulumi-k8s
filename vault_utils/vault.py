import random
import string
from typing import Optional

import pulumi
import pulumi_kubernetes as k8s


class Vault(pulumi.ComponentResource):
    __namespace = "vault"
    __version = "1.19.0"

    def __init__(
        self,
        name: str,
        namespace: str = "vault",
        props: Optional["pulumi.Inputs"] = None,
        opts: Optional[pulumi.ResourceOptions] = None,
        remote: bool = False,
    ) -> None:
        super().__init__("Vault", name, props, opts, remote)
        self.__namespace = namespace
        self.__opts = opts
        self.__operator = self.install_operator()
        self.__webhook = self.install_webhook()
        self.install_vault()

    def install_operator(self):
        return k8s.helm.v3.Release(
            "vault-operator",
            k8s.helm.v3.ReleaseArgs(
                chart="vault-operator",
                repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                    repo="https://kubernetes-charts.banzaicloud.com/",
                ),
                version=self.__version,
                namespace=self.__namespace,
                wait_for_jobs=True,
                replace=True,
                recreate_pods=True,
                cleanup_on_fail=True,
            ),
            opts=self.__opts,
        )

    def install_webhook(self):
        return k8s.helm.v3.Release(
            "webhook",
            k8s.helm.v3.ReleaseArgs(
                chart="vault-secrets-webhook",
                repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                    repo="https://kubernetes-charts.banzaicloud.com/",
                ),
                version=self.__version,
                namespace=self.__namespace,
                wait_for_jobs=True,
                replace=True,
                recreate_pods=True,
                cleanup_on_fail=True,
                values={
                    "podAnnotations": {
                        "linkerd.io/inject": "enabled",
                    },
                    "replicaCount": 1,
                    "certificate": {
                        "generate": True,
                        "userCertManager": True,
                    },
                },
            ),
            opts=self.__opts,
        )

    def install_vault(self):
        self.__vault_deployment = k8s.helm.v3.Release(
            "vault",
            k8s.helm.v3.ReleaseArgs(
                chart="vault",
                repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                    repo="https://kubernetes-charts.banzaicloud.com/",
                ),
                version=self.__version,
                namespace=self.__namespace,
                wait_for_jobs=True,
                cleanup_on_fail=True,
                values={
                    "persistence": {
                        "enabled": True,
                        "size": "1G",
                    },
                    "unsealer": {
                        "args": [
                            "--mode",
                            "k8s",
                            "--k8s-secret-namespace",
                            self.__namespace,
                            "--k8s-secret-name",
                            "bank-vaults",
                        ]
                    },
                    "vault": {
                        "externalConfig": {
                            "policies": [
                                {
                                    "name": "allow_secrets",
                                    "rules": """path "secret/*" {
                                                    capabilities = ["create",
                                                                    "read",
                                                                    "update",
                                                                    "delete",
                                                                    "list"]
                                                }""",
                                },
                                {
                                    "name": "hide_cubbyhole",
                                    "rules": """path "/cubbyhole/*" {capabilities = ["deny"]}""",
                                },
                            ],
                            "auth": [
                                {
                                    "type": "kubernetes",
                                    "roles": [
                                        {
                                            "name": "default",
                                            "bound_service_account_names": ["*"],
                                            "bound_service_account_namespaces": ["*"],
                                            "policies": ["allow_secrets"],
                                            "ttl": "1h",
                                        }
                                    ],
                                }
                            ],
                            "startupSecrets": [
                                {
                                    "type": "kv",
                                    "path": "secret/data/accounts/aws",
                                    "data": {
                                        "data": {
                                            "AWS_ACCESS_KEY_ID": "secretId",
                                            "AWS_SECRET_ACCESS_KEY": "s3cr3t",
                                        },
                                    },
                                },
                            ],
                        },
                    },
                },
            ),
            opts=pulumi.ResourceOptions(
                parent=self.__operator,
                depends_on=[self.__operator, self.__webhook],
            ),
        )
        return self.__vault_deployment

    def set_ingress(self, deps: list = []):
        service_name = self.__vault_deployment.resource_names.apply(
            lambda x: x.get("Service/v1")[0].split("/")[1]
        )
        k8s.networking.v1.Ingress(
            "vault-ingress",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                namespace=self.__namespace,
                annotations={
                    "nginx.ingress.kubernetes.io/service-upstream": "true",
                    "nginx.ingress.kubernetes.io/backend-protocol": "HTTPS",
                },
            ),
            spec=k8s.networking.v1.IngressSpecArgs(
                ingress_class_name="nginx",
                rules=[
                    k8s.networking.v1.IngressRuleArgs(
                        host="vault.thedodo.xyz",
                        http=k8s.networking.v1.HTTPIngressRuleValueArgs(
                            paths=[
                                k8s.networking.v1.HTTPIngressPathArgs(
                                    path="/",
                                    path_type="Prefix",
                                    backend=k8s.networking.v1.IngressBackendArgs(
                                        service=k8s.networking.v1.IngressServiceBackendArgs(
                                            name=service_name,
                                            port=k8s.networking.v1.ServiceBackendPortArgs(
                                                number=8200,
                                            ),
                                        )
                                    ),
                                )
                            ],
                        ),
                    )
                ],
            ),
            opts=pulumi.ResourceOptions(
                depends_on=deps,
            ),
        )

    def get_random_string(self, length):
        letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
        return "".join(random.choice(letters) for _ in range(length))
