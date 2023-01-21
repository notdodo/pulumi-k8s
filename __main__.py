# pyright: reportShadowedImports=false
import pulumi_kubernetes as k8s
from cni import cilium
from namespaces import namespaces
import csr
import metrics
import storageclass.openebs as openebs
import vault_utils.vault as vault

# import argocd.argocd as argocd

nss = namespaces.Namespaces()
nss.create_namespaces(["openebs", "vault", "cilium-system"])
network = cilium.init_cilium(nss.get_ns("cilium-system").name)
csr.auto_csr_approver(nss.get_ns("kube-system").name)
storage, storage_name = openebs.init(nss.get_ns("openebs").name, "openebs")
metrics.init_metrics_server(nss.get_ns("kube-system").name, deps=[network])
vault.init_vault(nss.get_ns("vault").name, storage_name, deps=[network, storage])

# nss.create_ns("argocd", fixed_name=True)
# argocd.init_argocd(nss.get_ns("argocd").name)
