"""
validate_k8s.py — Validate syntax and required fields of Kubernetes manifests
"""
import glob
import sys
import yaml

def validate():
    files = sorted(glob.glob("k8s/*.yaml"))
    if not files:
        print("❌ No yaml manifests found in k8s/")
        sys.exit(1)

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            docs = list(yaml.safe_load_all(f))
        for doc in docs:
            if not doc:
                continue
            assert "apiVersion" in doc, f"{path}: missing apiVersion"
            assert "kind" in doc, f"{path}: missing kind"
            assert "metadata" in doc and "name" in doc["metadata"], f"{path}: missing metadata.name"
            kind = doc["kind"]
            name = doc["metadata"]["name"]
            print(f"  [OK] Valid K8s manifest: {path} -> {kind}/{name}")

    print("[OK] All Kubernetes manifests are valid syntax and structure.")

if __name__ == "__main__":
    validate()
