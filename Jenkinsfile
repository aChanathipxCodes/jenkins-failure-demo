pipeline {
  agent any
  environment {
    REPORT_DIR = 'security-reports'
    PY_IMAGE   = 'python:3.11-slim'
    TRIVY_IMG  = 'aquasec/trivy:latest'
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
          docker run --rm -u root \
            -v "$WORKSPACE":/src -w /src ${PY_IMAGE} bash -lc '
              python -m pip install --no-cache-dir -q --upgrade pip &&
              pip install --no-cache-dir -q semgrep &&
              semgrep \
                --config=p/owasp-top-ten \
                --config=p/python \
                --include "**/*.py" \
                --severity ERROR \
                --sarif --output "/src/${REPORT_DIR}/semgrep.sarif" \
                --error
            '
          echo $? > "${REPORT_DIR}/semgrep.rc"
          set -e
        '''
      }
    }

    stage('Run Bandit (Python SAST)') {
      steps {
        sh '''
          set +e
          docker run --rm -u root \
            -v "$WORKSPACE":/src -w /src ${PY_IMAGE} bash -lc '
              python -m pip install --no-cache-dir -q --upgrade pip &&
              pip install --no-cache-dir -q bandit &&
              bandit -q -r . -f json -o "/src/${REPORT_DIR}/bandit.json"
            '
          echo $? > "${REPORT_DIR}/bandit.rc"
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
              -v "$WORKSPACE":/src -w /src ${PY_IMAGE} bash -lc '
                python -m pip install --no-cache-dir -q --upgrade pip &&
                pip install --no-cache-dir -q pip-audit &&
                (pip install --no-cache-dir -q -r requirements.txt || true) &&
                pip-audit -r requirements.txt -f json -o "/src/${REPORT_DIR}/pip-audit.json"
              '
            echo $? > "${REPORT_DIR}/pip-audit.rc"
          else
            echo 0 > "${REPORT_DIR}/pip-audit.rc"
          fi
          set -e
        '''
      }
    }

    stage('Run Trivy FS (Secrets & Config)') {
      steps {
        sh '''
          set +e
          docker run --rm -u root \
            -v "$WORKSPACE":/src -w /src ${TRIVY_IMG} \
            fs --scanners secret,config \
               --format sarif \
               --output "/src/${REPORT_DIR}/trivy.sarif" \
               --exit-code 1 --quiet /src
          echo $? > "${REPORT_DIR}/trivy.rc"
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
            if [ -f "${REPORT_DIR}/$f" ]; then
              v=$(cat "${REPORT_DIR}/$f")
              [ "$v" -ne 0 ] && echo "Fail flag from $f: $v" && FAIL=1
            fi
          done
          [ "$FAIL" -ne 0 ] && echo "Security checks failed." && exit 1 || echo "Security checks passed."
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
