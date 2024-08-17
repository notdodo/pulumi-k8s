# pyright: reportShadowedImports=false
import pulumi

import csr
import metrics
import network.ingress.ingress as ingress
import network.servicemesh.servicemesh as sm
import storageclass.openebs as openebs
import vault_utils.vault as vault
from namespaces import namespaces
from network import cilium

config = pulumi.Config()

nss = namespaces.Namespaces()
nss.create_namespaces(
    [
        {"name": "cert-manager", "generate_id": False},
        {"name": "cilium-system"},
        {"name": "nginx"},
        {"name": "openebs"},
        {"name": "vault"},
    ]
)

csr_approver = csr.auto_csr_approver(nss.get("kube-system").name)
network = cilium.init_cilium(nss.get("cilium-system").name)
# storage, storage_name = openebs.init(nss.get("openebs").name, "openebs")

metrics_srv = metrics.init_metrics_server(nss.get("kube-system").name)
kube_metrics = metrics.init_kube_state_metrics(nss.get("kube-system").name)

nginx = ingress.init_nginx(nss.get("nginx").name, deps=[csr_approver, network])

cert_mg = sm.cert_manager(nss.get("cert-manager").name, deps=[network])
# mesh = sm.init_linkerd(nss.get("linkerd").name, deps=[network, cert_mg])

vault_rsc = vault.Vault(
    "vault",
    nss.get("vault").name,
    opts=pulumi.ResourceOptions(depends_on=[network, cert_mg]),
)

vault_rsc.set_ingress(deps=[nginx, vault_rsc])
