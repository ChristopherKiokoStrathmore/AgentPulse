import math
from fastapi.testclient import TestClient
from main import app

def test_api_operational_invariants():
    with TestClient(app) as client:
        health=client.get("/health")
        assert health.status_code==200
        assert health.json()["outlets"]==30
        outlets=client.get("/v1/outlets").json()["data"]
        assert len(outlets)==30
        assert all(o["cash_kes"]>=0 and o["efloat_kes"]>=0 for o in outlets)
        check=client.get("/v1/ledger/check").json()
        assert check["balanced"]
        assert check["checked"]>0
        months=client.get("/v1/monthly").json()["data"]
        assert len(months)==36
        assert months[0]["period"]=="2023-11"
        assert months[-1]["period"]=="2026-10"
        assert client.get("/v1/transactions").status_code==200

def test_site_weights_and_persistence():
    with TestClient(app) as client:
        candidates=client.get("/v1/geo/candidates").json()["data"]
        assert len(candidates)==8
        default={"population":25,"commercial":20,"accessibility":15,"competition":15,
                 "economics":15,"coverage":10}
        response=client.post("/v1/geo/scores/preview",json={"weights":default})
        assert response.status_code==200
        scored=response.json()
        assert len(scored["data"])==8
        assert math.isclose(sum(scored["weights"].values()),1.0,abs_tol=0.0000001)
        assert scored["data"]==sorted(scored["data"],key=lambda s:s["score"],reverse=True)
        invalid=client.post("/v1/geo/scores/preview",json={"weights":{"population":0}})
        assert invalid.status_code==422
        created=client.post("/v1/geo/weight-profiles",json={"weights":default,"label":"Test weights"})
        assert created.status_code==200
        assert created.json()["persisted"] is True
        profiles=client.get("/v1/geo/weight-profiles")
        assert profiles.status_code==200
        assert any(p["id"]==created.json()["id"] for p in profiles.json()["data"])


def test_outlet_performance_36_month_history_and_missing_outlet():
    with TestClient(app) as client:
        response=client.get("/v1/outlets/AP-001/insights")
        assert response.status_code==200
        data=response.json()
        assert data["source"]=="synthetic"
        assert data["period"]=={"first":"2023-11","last":"2026-10","months":36}
        assert len(data["history"])==36
        assert all(m["transaction_count"]>0 and m["volume_kes"]>=0 for m in data["history"])
        assert data["summary"]["total_modelled_transactions"]==sum(
            month["transaction_count"] for month in data["history"]
        )
        assert data["summary"]["total_modelled_volume_kes"]==round(sum(
            month["volume_kes"] for month in data["history"]
        ),2)
        assert 0<len(data["recent_transactions"])<=60
        assert all(event["id"].startswith("SIM-001") for event in data["recent_transactions"])
        assert "not reconstructed from" in data["caveat"]
        assert client.get("/v1/outlets/DOES-NOT-EXIST/insights").status_code==404
