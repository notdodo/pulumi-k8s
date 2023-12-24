import pulumi_kubernetes as k8s


def auto_csr_approver(namespace: str):
    auto_csr_approved = k8s.helm.v3.Release(
        "kubelet-csr-approver",
        k8s.helm.v3.ReleaseArgs(
            chart="kubelet-csr-approver",
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://postfinance.github.io/kubelet-csr-approver/",
            ),
            version="1.0.6",
            namespace=namespace,
            values={
                "providerRegex": "k8s(master|worker)\d*",
                "providerIpPrefixed": "10.0.0.0/24,10.0.100.0/24,10.0.200.0/24,10.0.300.0/24,10.0.400.0/24",
                "allowedDNSNames": 10,
                "bypassDnsResolution": True,
                "bypassHostnameCheck": True,
                "loggingLevel": 10,
            },
        ),
    )
    return auto_csr_approved
