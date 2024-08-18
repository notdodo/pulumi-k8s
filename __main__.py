import pulumi

import csr
import metrics
import network as network
import network.servicemesh.servicemesh as sm
import vault_utils as vault
from namespaces import namespaces

config = pulumi.Config()

nss = namespaces.Namespaces()

cert_manager_ns = namespaces.Namespace(name="cert-manager", random_id=False)
cilium_system_ns = namespaces.Namespace(name="cilium-system")
nginx_ns = namespaces.Namespace(name="nginx")
openebs_ns = namespaces.Namespace(name="openebs")

csr_approver = csr.auto_csr_approver(nss.get("kube-system").name)
cilium = network.init_cilium(cilium_system_ns.name)
# storage, storage_name = openebs.init(nss.get("openebs").name, "openebs")

metrics_srv = metrics.init_metrics_server(nss.get("kube-system").name)
kube_metrics = metrics.init_kube_state_metrics(nss.get("kube-system").name)

nginx = network.init_nginx(nginx_ns.name, deps=[csr_approver, cilium])

cert_mg = sm.cert_manager(cert_manager_ns.name, deps=[cilium])
# mesh = sm.init_linkerd(nss.get("linkerd").name, deps=[network, cert_mg])

vault_rsc = vault.Vault(
    name="vault",
    namespace="vault",
    opts=pulumi.ResourceOptions(depends_on=[cilium, cert_mg]),
)

vault_rsc.set_ingress(deps=[nginx, vault_rsc])
