import pulumi_kubernetes as k8s


def auto_csr_approver(namespace: str):
    auto_csr_approved = k8s.helm.v3.Release(
        "kubelet-csr-approver",
        k8s.helm.v3.ReleaseArgs(
            chart="kubelet-csr-approver",
            repository_opts=k8s.helm.v3.RepositoryOptsArgs(
                repo="https://postfinance.github.io/kubelet-csr-approver/",
            ),
            namespace=namespace,
            values={
                "providerRegex": ".*",
                "allowedDNSNames": 10,
                "bypassDnsResolution": True,
                "bypassHostnameCheck": True,
                "providerIpPrefixes": "0.0.0.0/0,::/0",
                "loggingLevel": 10,
            },
        ),
    )
    return auto_csr_approved
