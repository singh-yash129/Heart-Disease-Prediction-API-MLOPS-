-- stress_test.lua — wrk Lua script for Deliverable 6
-- Sends POST /predict with realistic random patient data
-- Usage: wrk -t12 -c2000 -d30s -s src/stress_test.lua http://<EXTERNAL_IP>/predict

math.randomseed(os.time())

-- Helper: pick random from table
local function choice(t)
  return t[math.random(#t)]
end

-- Build request
wrk.method  = "POST"
wrk.headers["Content-Type"] = "application/json"

function request()
  local age      = math.random(29, 77)
  local gender   = choice({"male", "female"})
  local cp       = math.random(0, 3)
  local trestbps = math.random(94, 200)
  local chol     = math.random(126, 564)
  local fbs      = math.random(0, 1)
  local restecg  = math.random(0, 2)
  local thalach  = math.random(71, 202)
  local exang    = math.random(0, 1)
  -- oldpeak: 0.0 to 6.2, step 0.1
  local oldpeak  = math.random(0, 62) / 10.0
  local slope    = math.random(0, 2)
  local ca       = math.random(0, 3)
  local thal     = math.random(0, 3)

  local body = string.format(
    '{"age":%d,"gender":"%s","cp":%d,"trestbps":%d,"chol":%d,"fbs":%d,' ..
    '"restecg":%d,"thalach":%d,"exang":%d,"oldpeak":%.1f,"slope":%d,"ca":%d,"thal":%d}',
    age, gender, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal
  )
  return wrk.format(nil, nil, nil, body)
end

-- Response tracking
local success_count = 0
local error_count   = 0

function response(status, headers, body)
  if status == 200 then
    success_count = success_count + 1
  else
    error_count = error_count + 1
  end
end

function done(summary, latency, requests)
  io.write("\n===== Stress Test Results =====\n")
  io.write(string.format("Requests/sec   : %.2f\n", summary.requests / (summary.duration / 1e6)))
  io.write(string.format("Total requests : %d\n",   summary.requests))
  io.write(string.format("Success (200)  : %d\n",   success_count))
  io.write(string.format("Errors         : %d\n",   error_count + summary.errors.status))
  io.write(string.format("Timeouts       : %d\n",   summary.errors.timeout))
  io.write(string.format("Latency p50    : %.2f ms\n", latency:percentile(50)  / 1000))
  io.write(string.format("Latency p90    : %.2f ms\n", latency:percentile(90)  / 1000))
  io.write(string.format("Latency p99    : %.2f ms\n", latency:percentile(99)  / 1000))
  io.write(string.format("Latency p99.9  : %.2f ms\n", latency:percentile(99.9)/ 1000))
  io.write(string.format("Max latency    : %.2f ms\n", latency.max             / 1000))
  io.write("================================\n")
end
