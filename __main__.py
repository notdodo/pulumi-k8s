# pyright: reportShadowedImports=false
import re

import pulumi

import csr
import metrics
import network.ingress.ingress as ingress
import network.servicemesh.servicemesh as sm
import storageclass.openebs as openebs
import vault_utils.vault as vault
from namespaces import namespaces
from network import cilium

srv_re = re.compile(r"\/(.*)")

nss = namespaces.Namespaces()
nss.create_namespaces(
    [
        ["cilium-system", False],
        ["cert-manager", True],
        ["linkerd", True],
        ["openebs", False],
        # ["elk", False],
        ["vault", False],
        ["metallb", False],
        ["nginx", False],
    ]
)

network = cilium.init_cilium(nss.get("cilium-system").name)
csr.auto_csr_approver(nss.get("kube-system").name)
storage, storage_name = openebs.init(nss.get("openebs").name, "openebs")

lb = ingress.init_load_balancer(nss.get("metallb").name, deps=[network])
nginx = ingress.init_nginx(nss.get("nginx").name, deps=[network, lb])

metrics_srv = metrics.init_metrics_server(nss.get("kube-system").name, deps=[network])
kube_metrics = metrics.init_kube_state_metrics(
    nss.get("kube-system").name, deps=[network]
)

cert_mg = sm.cert_manager(nss.get("cert-manager").name, deps=[network])
# mesh = sm.init_linkerd(nss.get("linkerd").name, deps=[network, cert_mg])

vault_rsc = vault.Vault(
    "vault",
    nss.get("vault").name,
    opts=pulumi.ResourceOptions(depends_on=[network, storage, cert_mg]),
)

# vault_rsc.set_ingress()
