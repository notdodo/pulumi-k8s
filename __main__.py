# pyright: reportShadowedImports=false
import sys
import re
import pulumi
import pulumi_kubernetes as k8s
from network import cilium
from namespaces import namespaces
import metrics
import storageclass.openebs as openebs
import vault_utils.vault as vault
import network.servicemesh.servicemesh as sm

# import csr

sys.dont_write_bytecode = True
srv_re = re.compile(r"\/(.*)")

nss = namespaces.Namespaces()
nss.create_namespaces(
    [
        ["cilium-system", False],
        ["cert-manager", True],
        ["linkerd", True],
        ["openebs", False],
        ["elk", False],
        ["vault", False],
        ["nginx", False],
    ]
)

storage, storage_name = openebs.init(nss.get("openebs").name, "openebs")
network = cilium.init_cilium(nss.get("cilium-system").name)
# csr.auto_csr_approver(nss.get("kube-system").name)
metrics_srv = metrics.init_metrics_server(nss.get("kube-system").name, deps=[network])
kube_metrics = metrics.init_kube_state_metrics(
    nss.get("kube-system").name, deps=[network]
)
cert_mg = sm.cert_manager(nss.get("cert-manager").name, deps=[network])
mesh = sm.init_linkerd(nss.get("linkerd").name, deps=[network, cert_mg])
vault_srv = vault.init_vault(nss.get("vault").name, deps=[network, storage, mesh])


def set_namespace(obj, opts=None):
    if isinstance(obj, list):
        for i in obj:
            set_namespace(i)
    elif isinstance(obj, dict):
        for k in obj:
            if k == "xpack.fleet.agentPolicies":
                continue
            if k == "namespace":
                obj[k] = nss.get("elk").name
            elif isinstance(obj, dict):
                set_namespace(obj[k])


k8s.yaml.ConfigFile("eck-definition", file="./crds/eck-crds.yaml")

certManager = k8s.yaml.ConfigFile(
    "eck-operator", file="./crds/eck-operator.yaml", transformations=[set_namespace]
)

eck = k8s.yaml.ConfigFile(
    "eck", file="./crds/eck.yaml", transformations=[set_namespace]
)

nginx = k8s.helm.v3.Release(
    "nginx",
    k8s.helm.v3.ReleaseArgs(
        chart="ingress-nginx",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://kubernetes.github.io/ingress-nginx",
        ),
        namespace=nss.get("nginx").name,
        cleanup_on_fail=True,
        values={
            "controller": {
                "hostPort": {"enabled": True},
                "service": {
                    "type": "NodePort",
                },
                "podAnnotations": {
                    "linkerd.io/inject": "enabled",
                },
            },
            "rbac": {"create": True},
            "annotations": {
                "linkerd.io/inject": "enabled",
            },
        },
    ),
    opts=pulumi.ResourceOptions(depends_on=mesh),
)

k8s.networking.v1.Ingress(
    "elastic-agent-ingress",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        namespace=nss.get("elk").name,
        annotations={
            "nginx.ingress.kubernetes.io/service-upstream": "true",
            "nginx.ingress.kubernetes.io/backend-protocol": "HTTPS",
            "nginx.ingress.kubernetes.io/secure-backends": "true",
            "nginx.ingress.kubernetes.io/rewrite-target": "/$2",
        },
    ),
    spec=k8s.networking.v1.IngressSpecArgs(
        ingress_class_name="nginx",
        rules=[
            k8s.networking.v1.IngressRuleArgs(
                host="elk.thedodo.xyz",
                http=k8s.networking.v1.HTTPIngressRuleValueArgs(
                    paths=[
                        k8s.networking.v1.HTTPIngressPathArgs(
                            path="/elastic-agent-es(/|$)(.*)",
                            path_type="Prefix",
                            backend=k8s.networking.v1.IngressBackendArgs(
                                service=k8s.networking.v1.IngressServiceBackendArgs(
                                    name="elasticsearch-es-http",
                                    port=k8s.networking.v1.ServiceBackendPortArgs(
                                        number=9200
                                    ),
                                )
                            ),
                        ),
                        k8s.networking.v1.HTTPIngressPathArgs(
                            path="/fleet-server(/|$)(.*)",
                            path_type="Prefix",
                            backend=k8s.networking.v1.IngressBackendArgs(
                                service=k8s.networking.v1.IngressServiceBackendArgs(
                                    name="fleet-server-agent-http",
                                    port=k8s.networking.v1.ServiceBackendPortArgs(
                                        number=8220
                                    ),
                                )
                            ),
                        ),
                    ]
                ),
            )
        ],
    ),
    opts=pulumi.ResourceOptions(depends_on=[nginx]),
)

k8s.networking.v1.Ingress(
    "elk",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        namespace=nss.get("elk").name,
        annotations={
            "nginx.ingress.kubernetes.io/service-upstream": "true",
            "nginx.ingress.kubernetes.io/backend-protocol": "HTTPS",
            "nginx.ingress.kubernetes.io/secure-backends": "true",
            "nginx.ingress.kubernetes.io/proxy-body-size": "8m",
            "nginx.ingress.kubernetes.io/force-ssl-redirect": "true",
        },
    ),
    spec=k8s.networking.v1.IngressSpecArgs(
        ingress_class_name="nginx",
        rules=[
            k8s.networking.v1.IngressRuleArgs(
                host="elk.thedodo.xyz",
                http=k8s.networking.v1.HTTPIngressRuleValueArgs(
                    paths=[
                        k8s.networking.v1.HTTPIngressPathArgs(
                            path="/",
                            path_type="Prefix",
                            backend=k8s.networking.v1.IngressBackendArgs(
                                service=k8s.networking.v1.IngressServiceBackendArgs(
                                    name="kibana-kb-http",
                                    port=k8s.networking.v1.ServiceBackendPortArgs(
                                        number=5601
                                    ),
                                )
                            ),
                        ),
                    ]
                ),
            )
        ],
    ),
    opts=pulumi.ResourceOptions(depends_on=[nginx]),
)

k8s.networking.v1.Ingress(
    "vault-ingress",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        namespace=nss.get("vault").name,
        annotations={
            # "nginx.ingress.kubernetes.io/service-upstream": "true",
            "nginx.ingress.kubernetes.io/force-ssl-redirect": "true",
            "nginx.ingress.kubernetes.io/ssl-passthrough": "false",
            # "cert-manager.io/cluster-issuer": "letsencrypt-prod",
            # "kubernetes.io/tls-acme": "true",
        },
    ),
    spec=k8s.networking.v1.IngressSpecArgs(
        # tls=[
        #     k8s.networking.v1.IngressTLSArgs(
        #         hosts=["vault.thedodo.xyz"],
        #         secret_name="cloudflare-api-token-secret",
        #     )
        # ],
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
                                    name=vault_srv.apply(
                                        lambda v: srv_re.findall(v)[0]
                                    ),
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
    opts=pulumi.ResourceOptions(depends_on=[nginx]),
)
