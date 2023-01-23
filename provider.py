import pulumi_kubernetes as k8s

provider = k8s.Provider("k8s", enable_server_side_apply=True)
