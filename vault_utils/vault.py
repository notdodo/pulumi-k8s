import random
import string
from typing import Optional

import pulumi
import pulumi_kubernetes as k8s


class Vault(pulumi.ComponentResource):
    __namespace = "vault"

    def __init__(
        self,
        # t: str,
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
        self.__opts.depends_on.append(self.__operator)  # pyright: ignore
        self.__webhook = self.install_webhook()
        self.__opts.depends_on.append(self.__webhook)  # pyright: ignore
        self.install_vault()
        # pulumi.export("test", "1234")
        # this_stack = pulumi.StackReference("notdodo/pulumi-k8s/pulumi-k8s")
        # exported_bucket_name = this_stack.get_output("test")
        # exported_bucket_name.apply(lambda x: print(x))

    def install_operator(self):
        return k8s.helm.v3.Release(
            "vault-operator",
            k8s.helm.v3.ReleaseArgs(
                chart="vault-operator",
                repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                    repo="https://kubernetes-charts.banzaicloud.com/",
                ),
                version="1.19.0",
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
                version="1.19.0",
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

    def __set_namespace(self, obj, opts=None):
        if isinstance(obj, list):
            for i in obj:
                self.__set_namespace(i)
        elif isinstance(obj, dict):
            for k in obj:
                if k == "xpack.fleet.agentPolicies":
                    continue
                elif k == "namespace" or k == "secretNamespace":
                    obj[k] = self.__namespace
                elif k == "startupSecrets":
                    obj[k] = self.STARTUP_SECRETS
                elif isinstance(obj, dict):
                    self.__set_namespace(obj[k])

    def install_vault(self):
        self.__init_default_secrets()
        return k8s.yaml.ConfigFile(
            "vault",
            file="./vault_utils/vault.yaml",
            transformations=[self.__set_namespace],
            opts=self.__opts,
        )

    def __init_default_secrets(self):
        self.STARTUP_SECRETS = [
            {
                "type": "kv",
                "path": "secret/data/accounts/kibana",
                "data": {
                    "data": {"password": "TODOKIBANASECRET"},  # TODO FIXME
                },
            }
        ]

    def set_ingress(self):
        k8s.networking.v1.Ingress(
            "vault-ingress",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                namespace=self.__namespace,
                annotations={
                    "nginx.ingress.kubernetes.io/service-upstream": "true",
                    "nginx.ingress.kubernetes.io/force-ssl-redirect": "true",
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
                                            name="vault-0",
                                            port=k8s.networking.v1.ServiceBackendPortArgs(
                                                number=8200
                                            ),
                                        )
                                    ),
                                )
                            ],
                        ),
                    )
                ],
            ),
        )

    def get_random_string(self, length):
        letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
        return "".join(random.choice(letters) for i in range(length))
