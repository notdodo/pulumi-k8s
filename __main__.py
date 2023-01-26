# pyright: reportShadowedImports=false
import pulumi_kubernetes as k8s
from cni import cilium
from namespaces import namespaces
import csr
import metrics
import storageclass.openebs as openebs
import vault_utils.vault as vault
import servicemesh.servicemesh as sm

# import argocd.argocd as argocd

nss = namespaces.Namespaces()
nss.create_namespaces(
    [
        ["openebs", False],
        ["vault", False],
        ["cilium-system", False],
        ["cert-manager", True],
        ["linkerd", True],
        ["elk", False],
    ]
)
network = cilium.init_cilium(nss.get_ns("cilium-system").name)
csr.auto_csr_approver(nss.get_ns("kube-system").name)
storage, storage_name = openebs.init(nss.get_ns("openebs").name, "openebs")
metrics_srv = metrics.init_metrics_server(
    nss.get_ns("kube-system").name, deps=[network]
)
cert_mg = sm.cert_manager(nss.get_ns("cert-manager").name, deps=[network])
mesh = sm.init_linkerd(nss.get_ns("linkerd").name, deps=[network, cert_mg])
vault.init_vault(nss.get_ns("vault").name, storage_name, deps=[network, storage, mesh])

# nss.create_ns("argocd", fixed_name=True)
# argocd.init_argocd(nss.get_ns("argocd").name)


import pulumi

elk = k8s.helm.v3.Release(
    "elk",
    k8s.helm.v3.ReleaseArgs(
        chart="elasticsearch",
        repository_opts=k8s.helm.v3.RepositoryOptsArgs(
            repo="https://helm.elastic.co",
        ),
        namespace=nss.get_ns("elk").name,
        wait_for_jobs=True,
        cleanup_on_fail=True,
        values={
            "replicas": 1,
            "antiAffinity": "soft",
            "minimumMasterNodes": 0,
            # "esJavaOpts": "-Xmx128m -Xms128m",
            "resources": {
                "requests": {
                    "cpu": "500m",
                    "memory": "1000M",
                },
                "limits": {
                    "cpu": "1000m",
                    "memory": "2048M",
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
        namespace=nss.get_ns("elk").name,
        wait_for_jobs=True,
        cleanup_on_fail=True,
    ),
    opts=pulumi.ResourceOptions(parent=elk, depends_on=elk),
)
