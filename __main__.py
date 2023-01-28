# pyright: reportShadowedImports=false
import sys

sys.dont_write_bytecode = True

import pulumi_kubernetes as k8s
from network import cilium
from namespaces import namespaces
import csr
import metrics
import storageclass.openebs as openebs
import vault_utils.vault as vault
import network.servicemesh.servicemesh as sm
import re

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

# nss.annotate(nss.get("vault").name, "vault_ann")

storage, storage_name = openebs.init(nss.get("openebs").name, "openebs")
network = cilium.init_cilium(nss.get("cilium-system").name)
csr.auto_csr_approver(nss.get("kube-system").name)
metrics_srv = metrics.init_metrics_server(nss.get("kube-system").name, deps=[network])
cert_mg = sm.cert_manager(nss.get("cert-manager").name, deps=[network])
mesh = sm.init_linkerd(nss.get("linkerd").name, deps=[network, cert_mg])
vault_srv = vault.init_vault(nss.get("vault").name, deps=[network, storage, mesh])

import pulumi

elk = k8s.helm.v3.Release(
    "elk",
    k8s.helm.v3.ReleaseArgs(
        chart="elasticsearch",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://helm.elastic.co",
        ),
        namespace=nss.get("elk").name,
        wait_for_jobs=True,
        cleanup_on_fail=True,
        # https://github.com/elastic/helm-charts/blob/main/elasticsearch/values.yaml
        values={
            "podAnnotations": {
                "linkerd.io/inject": "enabled",
            },
            "service": {
                "annotations": {"linkerd.io/inject": "enabled"},
            },
            "replicas": 1,
            "antiAffinity": "soft",
            "minimumMasterNodes": 0,
            # "esJavaOpts": "-Xmx128m -Xms128m",
            "resources": {
                "requests": {
                    "cpu": "500m",
                    "memory": "2048M",
                },
                "limits": {
                    "cpu": "1000m",
                    "memory": "4096M",
                },
            },
        },
    ),
    opts=pulumi.ResourceOptions(depends_on=mesh),
)

kibana = k8s.helm.v3.Release(
    "kibana",
    k8s.helm.v3.ReleaseArgs(
        chart="kibana",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://helm.elastic.co",
        ),
        namespace=nss.get("elk").name,
        wait_for_jobs=True,
        cleanup_on_fail=True,
        values={
            "podAnnotations": {
                "linkerd.io/inject": "enabled",
            },
        },
    ),
    opts=pulumi.ResourceOptions(parent=elk, depends_on=elk),
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
        },
    ),
    opts=pulumi.ResourceOptions(depends_on=mesh),
)


kibana_srv = kibana.resource_names["Service/v1"][0]

k8s.networking.v1.Ingress(
    "elk-ingress",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        namespace=nss.get("elk").name,
        annotations={
            "nginx.ingress.kubernetes.io/service-upstream": "true",
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
                                    name=kibana_srv,
                                    port=k8s.networking.v1.ServiceBackendPortArgs(
                                        number=5601
                                    ),
                                )
                            ),
                        )
                    ]
                ),
            )
        ],
    ),
    opts=pulumi.ResourceOptions(depends_on=[nginx, kibana]),
)

k8s.networking.v1.Ingress(
    "vault-ingress",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        namespace=nss.get("vault").name,
        annotations={
            "nginx.ingress.kubernetes.io/service-upstream": "true",
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
                                    name=vault_srv.apply(
                                        lambda v: srv_re.findall(v)[0]
                                    ),
                                    port=k8s.networking.v1.ServiceBackendPortArgs(
                                        number=8200
                                    ),
                                )
                            ),
                        )
                    ]
                ),
            )
        ],
    ),
    opts=pulumi.ResourceOptions(depends_on=[nginx]),
)
