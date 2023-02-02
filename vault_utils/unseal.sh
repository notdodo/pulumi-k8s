#!/usr/bin/env bash

NAMESPACE=$(kubectl get ns --no-headers -o custom-columns=':metadata.name' | grep vault-)
if [ $? -ne 0 ]; then echo "No running vault"; exit 0; fi

POD=$(kubectl get pods -n "${NAMESPACE}" --no-headers -o custom-columns=':metadata.name' -l app.kubernetes.io/name=vault)
kubectl wait pods -n "${NAMESPACE}" -l app.kubernetes.io/name=vault --for condition=Ready=False --for condition=Initialized=True --for condition=Ready=False --for condition=PodScheduled=True --timeout=90s  > /dev/null 2>&1

if ! kubectl exec "${POD}" -n "${NAMESPACE}" -- vault status 2> /dev/null | grep "Sealed" | grep -q 'true'; then echo "Not Sealed"; exit 0; fi

UNSEAL_KEYS="$(kubectl exec "${POD}" -n "${NAMESPACE}" -- vault operator init 2> /dev/null)"
mapfile -t keys < <(printf "%s" "${UNSEAL_KEYS}" | grep 'Unseal Key ' | awk -F " " '{print $4}')
for key in "${keys[@]}"; do
    kubectl exec "${POD}" -n "${NAMESPACE}" -- vault operator unseal "${key}" > /dev/null 2>&1
done

ROOT_TOKEN=$(grep "Initial Root Token" <<< "${UNSEAL_KEYS}" | awk -F " " '{print $4}')
echo "${ROOT_TOKEN}"

