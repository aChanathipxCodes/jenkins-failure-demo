pipeline {
  agent any
  environment {
    REPORT_DIR = 'security-reports'
  }
  options { timestamps() }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh 'mkdir -p ${REPORT_DIR}'
      }
    }

    stage('Run Semgrep (OWASP + Python)') {
      steps {
        sh '''
          set +e
          docker run --rm -u root \
            -v "$PWD":/src -w /src python:3.11-slim bash -lc '
              python -m pip -q install --upgrade pip &&
              pip -q install semgrep &&
              semgrep scan --no-git \
                --config=p/owasp-top-ten --config=p/python \
                --include "**/*.py" \
                --severity ERROR \
                --sarif --output "/src/${REPORT_DIR}/semgrep.sarif" \
                --error
            '
          SEM_RC=$?
          echo $SEM_RC > "${REPORT_DIR}/semgrep.rc"
          set -e
        '''
      }
    }

    stage('Run Bandit (Python SAST)') {
      steps {
        sh '''
          set +e
          docker run --rm -u root \
            -v "$PWD":/src -w /src python:3.11-slim bash -lc '
              python -m pip -q install --upgrade pip &&
              pip -q install bandit &&
              bandit -q -r . -f json -o "/src/${REPORT_DIR}/bandit.json" || true &&
              python - <<PY
import json, sys
p="security-reports/bandit.json"
try:
    d=json.load(open(p))
    findings=len(d.get("results", []))
    print("bandit findings:", findings)
    sys.exit(1 if findings>0 else 0)
except Exception as e:
    print("bandit parse error:", e)
    sys.exit(0)
PY
            '
          BANDIT_RC=$?
          echo $BANDIT_RC > "${REPORT_DIR}/bandit.rc"
          set -e
        '''
      }
    }

    stage('Run pip-audit (Dependencies)') {
      steps {
        sh '''
          set +e
          if [ -f requirements.txt ]; then
            docker run --rm -u root \
              -v "$PWD":/src -w /src python:3.11-slim bash -lc '
                python -m pip -q install --upgrade pip &&
                pip -q install pip-audit &&
                (pip -q install -r requirements.txt || true) &&
                pip-audit -r requirements.txt -f json -o "/src/${REPORT_DIR}/pip-audit.json"
              '
            PA_RC=$?
          else
            echo "no requirements.txt -> skip pip-audit"
            PA_RC=0
          fi
          echo $PA_RC > "${REPORT_DIR}/pip-audit.rc"
          set -e
        '''
      }
    }

    stage('Run Trivy FS (Secrets & Config)') {
      steps {
        sh '''
          set +e
          docker run --rm -u root \
            -v "$PWD":/src -w /src aquasec/trivy:latest \
            fs --scanners secret,config \
               --format sarif \
               --output /src/${REPORT_DIR}/trivy.sarif \
               --exit-code 1 --quiet /src
          TRIVY_RC=$?
          echo $TRIVY_RC > "${REPORT_DIR}/trivy.rc"
          set -e
        '''
      }
    }

    stage('Decide') {
      steps {
        sh '''
          set -e
          FAIL=0
          for f in semgrep.rc bandit.rc pip-audit.rc trivy.rc; do
            [ -f "${REPORT_DIR}/$f" ] || echo 0 > "${REPORT_DIR}/$f"
            v=$(cat "${REPORT_DIR}/$f" || echo 0)
            if [ "$v" -ne 0 ]; then
              echo "Fail flag from $f: $v"
              FAIL=1
            fi
          done
          if [ "$FAIL" -ne 0 ]; then
            echo "Security checks failed."
            exit 1
          else
            echo "Security checks passed."
          fi
        '''
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: "${REPORT_DIR}/**", fingerprint: true
      echo "Scan completed. Reports archived in ${REPORT_DIR}/"
    }
  }
}
