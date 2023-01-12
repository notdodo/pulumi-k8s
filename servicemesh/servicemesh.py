def init_sm():
    pass


# OSM doesn't work with cilium as CNI
# osm = k8s.helm.v3.Release(
#     "osm",
#     k8s.helm.v3.ReleaseArgs(
#         chart="osm",
#         repository_opts=k8s.helm.v3.RepositoryOptsArgs(
#             repo="https://openservicemesh.github.io/osm",
#         ),
#         namespace=nss.get_ns("osm").name,
#         values={
#             "osm": {
#                 "trustDomain": "dodo.local",
#                 "enablePermissiveTrafficPolicy": True,
#                 "deployPrometheus": True,
#                 "deployGrafana": True,
#                 "deployJaeger": True,
#                 "tracing": {"enable": True},
#             },
#         },
#     ),
# )
