pipeline {
  agent any
  environment {
    REPORT_DIR = 'security-reports'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh 'mkdir -p "$REPORT_DIR"'
      }
    }

    stage('Run Semgrep (OWASP + Python)') {
      steps {
        sh '''
          set +e
          docker run --rm -u root -v "$PWD":/src -w /src python:3.11-slim bash -lc '
            python -m pip install --no-cache-dir -q --upgrade pip &&
            pip install --no-cache-dir -q semgrep &&
            semgrep --config=p/owasp-top-ten --config=p/python \
                    --severity ERROR \
                    --sarif --output /src/'"$REPORT_DIR"'/semgrep.sarif \
                    --error
          '
          SEMGREP_RC=$?
          echo $SEMGREP_RC > "$REPORT_DIR/semgrep.rc"
          exit 0
        '''
      }
    }

    stage('Run Bandit (Python SAST)') {
      steps {
        sh '''
          set +e
          docker run --rm -u root -v "$PWD":/src -w /src python:3.11-slim bash -lc '
            python -m pip install --no-cache-dir -q --upgrade pip &&
            pip install --no-cache-dir -q bandit &&
            bandit -q -r . -f sarif -o /src/'"$REPORT_DIR"'/bandit.sarif || true
          '
          echo 0 > "$REPORT_DIR/bandit.rc"
          exit 0
        '''
      }
    }

    stage('Run pip-audit (Dependencies)') {
      steps {
        sh '''
          set +e
          if [ -f requirements.txt ]; then
            docker run --rm -u root -v "$PWD":/src -w /src python:3.11-slim bash -lc '
              python -m pip install --no-cache-dir -q --upgrade pip &&
              pip install --no-cache-dir -q pip-audit &&
              # ติดตั้งให้ครบเพื่อไม่เกิด false-positive จาก pkg ที่ยังไม่ลง
              (pip install --no-cache-dir -q -r requirements.txt || true) &&
              pip-audit -r requirements.txt -f json -o /src/'"$REPORT_DIR"'/pip-audit.json || true
            '
          else
            echo '{"results":[]}' > "$REPORT_DIR/pip-audit.json"
          fi
          echo 0 > "$REPORT_DIR/pip-audit.rc"
          exit 0
        '''
      }
    }

    stage('Run Trivy FS (Secrets & Config)') {
      steps {
        sh '''
          set +e
          docker run --rm -u root -v "$PWD":/src -w /src aquasec/trivy:latest fs \
            --scanners secret,config \
            --format sarif --output /src/'"$REPORT_DIR"'/trivy.sarif \
            --exit-code 1 --quiet /src
          TRIVY_RC=$?
          echo $TRIVY_RC > "$REPORT_DIR/trivy.rc"
          exit 0
        '''
      }
    }

    stage('Decide') {
      steps {
        sh '''
          set -e
          FAIL=0
          for f in "$REPORT_DIR"/*.rc; do
            [ -f "$f" ] || continue
            v=$(cat "$f" 2>/dev/null || echo 0)
            if [ "$v" -ne 0 ]; then
              echo "Fail flag from $(basename "$f"): $v"
              FAIL=1
            fi
          done

          if [ "$FAIL" -ne 0 ]; then
            echo "Security checks failed."
            exit 1
          else
            echo "All security checks passed."
          fi
        '''
      }
    }
  }

  post {
    always {
      archiveArtifacts artifacts: 'security-reports/**', fingerprint: false, allowEmptyArchive: true
      echo 'Scan completed. Reports archived in security-reports/'
    }
  }
}
