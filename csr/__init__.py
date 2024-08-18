from typing import Any, Union

from pulumi import Output
from pulumi_kubernetes import helm


def auto_csr_approver(namespace: Union[str, Output[Any]]) -> helm.v3.Release:
    auto_csr_approved = helm.v3.Release(
        "kubelet-csr-approver",
        helm.v3.ReleaseArgs(
            chart="kubelet-csr-approver",
            repository_opts=helm.v3.RepositoryOptsArgs(
                repo="https://postfinance.github.io/kubelet-csr-approver/",
            ),
            version="1.2.2",
            namespace=namespace,
            values={
                "providerRegex": r"dev-.*",
                # "providerIpPrefixed": "10.0.0.0/24,10.0.100.0/24,10.0.200.0/24,10.0.300.0/24,10.0.400.0/24",
                "allowedDNSNames": 10,
                # "bypassDnsResolution": True,
                # "bypassHostnameCheck": True,
                "loggingLevel": 10,
            },
        ),
    )
    return auto_csr_approved
