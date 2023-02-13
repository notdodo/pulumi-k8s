# def set_namespace(obj, opts=None):
#     if isinstance(obj, list):
#         for i in obj:
#             set_namespace(i)
#     elif isinstance(obj, dict):
#         for k in obj:
#             if k == "xpack.fleet.agentPolicies":
#                 continue
#             if k == "namespace":
#                 obj[k] = nss.get("elk").name
#             elif isinstance(obj, dict):
#                 set_namespace(obj[k])


# k8s.yaml.ConfigFile("eck-definition", file="./crds/eck-crds.yaml")

# certManager = k8s.yaml.ConfigFile(
#     "eck-operator", file="./crds/eck-operator.yaml", transformations=[set_namespace]
# )

# eck = k8s.yaml.ConfigFile(
#     "eck", file="./crds/eck.yaml", transformations=[set_namespace]
# )

# k8s.networking.v1.Ingress(
#     "elastic-agent-ingress",
#     metadata=k8s.meta.v1.ObjectMetaArgs(
#         namespace=nss.get("elk").name,
#         annotations={
#             "nginx.ingress.kubernetes.io/service-upstream": "true",
#             "nginx.ingress.kubernetes.io/backend-protocol": "HTTPS",
#             "nginx.ingress.kubernetes.io/secure-backends": "true",
#             "nginx.ingress.kubernetes.io/rewrite-target": "/$2",
#         },
#     ),
#     spec=k8s.networking.v1.IngressSpecArgs(
#         ingress_class_name="nginx",
#         rules=[
#             k8s.networking.v1.IngressRuleArgs(
#                 host="elk.thedodo.xyz",
#                 http=k8s.networking.v1.HTTPIngressRuleValueArgs(
#                     paths=[
#                         k8s.networking.v1.HTTPIngressPathArgs(
#                             path="/elastic-agent-es(/|$)(.*)",
#                             path_type="Prefix",
#                             backend=k8s.networking.v1.IngressBackendArgs(
#                                 service=k8s.networking.v1.IngressServiceBackendArgs(
#                                     name="elasticsearch-es-http",
#                                     port=k8s.networking.v1.ServiceBackendPortArgs(
#                                         number=9200
#                                     ),
#                                 )
#                             ),
#                         ),
#                         k8s.networking.v1.HTTPIngressPathArgs(
#                             path="/fleet-server(/|$)(.*)",
#                             path_type="Prefix",
#                             backend=k8s.networking.v1.IngressBackendArgs(
#                                 service=k8s.networking.v1.IngressServiceBackendArgs(
#                                     name="fleet-server-agent-http",
#                                     port=k8s.networking.v1.ServiceBackendPortArgs(
#                                         number=8220
#                                     ),
#                                 )
#                             ),
#                         ),
#                     ]
#                 ),
#             )
#         ],
#     ),
#     opts=pulumi.ResourceOptions(depends_on=[nginx]),
# )

# k8s.networking.v1.Ingress(
#     "elk",
#     metadata=k8s.meta.v1.ObjectMetaArgs(
#         namespace=nss.get("elk").name,
#         annotations={
#             "nginx.ingress.kubernetes.io/service-upstream": "true",
#             "nginx.ingress.kubernetes.io/backend-protocol": "HTTPS",
#             "nginx.ingress.kubernetes.io/secure-backends": "true",
#             "nginx.ingress.kubernetes.io/proxy-body-size": "8m",
#             "nginx.ingress.kubernetes.io/force-ssl-redirect": "true",
#         },
#     ),
#     spec=k8s.networking.v1.IngressSpecArgs(
#         ingress_class_name="nginx",
#         rules=[
#             k8s.networking.v1.IngressRuleArgs(
#                 host="elk.thedodo.xyz",
#                 http=k8s.networking.v1.HTTPIngressRuleValueArgs(
#                     paths=[
#                         k8s.networking.v1.HTTPIngressPathArgs(
#                             path="/",
#                             path_type="Prefix",
#                             backend=k8s.networking.v1.IngressBackendArgs(
#                                 service=k8s.networking.v1.IngressServiceBackendArgs(
#                                     name="kibana-kb-http",
#                                     port=k8s.networking.v1.ServiceBackendPortArgs(
#                                         number=5601
#                                     ),
#                                 )
#                             ),
#                         ),
#                     ]
#                 ),
#             )
#         ],
#     ),
#     opts=pulumi.ResourceOptions(depends_on=[nginx]),
# )
