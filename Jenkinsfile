pipeline {
  agent any
  options { timestamps() }
  environment {
    REPORT_DIR = 'security-reports'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh 'mkdir -p ${REPORT_DIR}'
        sh 'echo "Workspace files:" && ls -la'
      }
    }

    stage('Run Semgrep (OWASP + Python)') {
      steps {
        sh '''#!/bin/bash -e
          set +e
          docker run --rm -u root \
            -v "$PWD":/src -w /src python:3.11-slim bash -lc '
              python -m pip install -q --upgrade pip &&
              pip install -q semgrep &&
              semgrep \
                --config=p/owasp-top-ten \
                --config=p/python \
                --include "**/*.py" \
                --sarif --output "/src/${REPORT_DIR}/semgrep.sarif" \
                --error
            '
          echo $? > ${REPORT_DIR}/semgrep.rc
          set -e
        '''
      }
    }

    stage('Run Bandit (Python SAST)') {
      steps {
        sh '''#!/bin/bash -e
          set +e
          docker run --rm -u root \
            -v "$PWD":/src -w /src python:3.11-slim bash -lc '
              python -m pip install -q --upgrade pip &&
              pip install -q bandit &&
              bandit -q -r . -f json -o "/src/${REPORT_DIR}/bandit.json"
            '
          echo $? > ${REPORT_DIR}/bandit.rc
          set -e
        '''
      }
    }

    stage('Run pip-audit (Dependencies)') {
      steps {
        sh '''#!/bin/bash -e
          set +e
          if [ -f requirements.txt ]; then
            docker run --rm -u root \
              -v "$PWD":/src -w /src python:3.11-slim bash -lc '
                python -m pip install -q --upgrade pip &&
                pip install -q pip-audit &&
                (pip install -q -r requirements.txt || true) &&
                pip-audit -r requirements.txt -f json -o "/src/${REPORT_DIR}/pip-audit.json"
              '
            echo $? > ${REPORT_DIR}/pip-audit.rc
          else
            echo "requirements.txt not found; skipping pip-audit."
            echo 0 > ${REPORT_DIR}/pip-audit.rc
          fi
          set -e
        '''
      }
    }

    stage('Run Trivy FS (Secrets & Config)') {
      steps {
        sh '''#!/bin/bash -e
          set +e
          docker run --rm -u root \
            -v "$PWD":/src -w /src aquasec/trivy:latest \
              fs --scanners secret,config \
              --format sarif \
              --output "/src/${REPORT_DIR}/trivy.sarif" \
              --quiet /src
          echo $? > ${REPORT_DIR}/trivy.rc
          set -e
        '''
      }
    }

    stage('Decide') {
      steps {
        sh '''#!/bin/bash -e
          FAIL=0

          if [ -f ${REPORT_DIR}/semgrep.rc ]; then
            v=$(cat ${REPORT_DIR}/semgrep.rc)
            if [ "$v" -ne 0 ]; then
              echo "Fail flag from semgrep.rc: $v"
              FAIL=1
            fi
          fi

          # ตัวอื่นๆ เป็นข้อมูลประกอบ ไม่ชี้ขาดผลสุดท้าย
          echo "Bandit RC: $(cat ${REPORT_DIR}/bandit.rc 2>/dev/null || echo N/A)"
          echo "pip-audit RC: $(cat ${REPORT_DIR}/pip-audit.rc 2>/dev/null || echo N/A)"
          echo "Trivy RC: $(cat ${REPORT_DIR}/trivy.rc 2>/dev/null || echo N/A)"

          if [ "$FAIL" -ne 0 ]; then
            echo "Security checks failed (based on Semgrep)."
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
      archiveArtifacts artifacts: "${REPORT_DIR}/**/*", allowEmptyArchive: true, fingerprint: true
      echo "Scan completed. Reports archived in ${REPORT_DIR}/"
    }
  }
}
