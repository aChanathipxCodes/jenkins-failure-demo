pipeline {
  agent any

  environment {
    REPORT_DIR = 'security-reports'
  }

  options { timestamps() }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Prepare workspace') {
      steps { sh 'mkdir -p "$REPORT_DIR"' }
    }

    stage('Semgrep (OWASP + Python)') {
      steps {
        // เจอ ERROR แล้วออก non-zero (ล้ม)
        sh '''
          docker run --rm \
            -v "$PWD":/ws -w /ws \
            returntocorp/semgrep:latest \
              semgrep \
                --config=p/owasp-top-ten \
                --config=p/python \
                --severity "ERROR" \
                --sarif --output "$REPORT_DIR/semgrep.sarif" \
                --error
        '''
      }
    }

    stage('Bandit (Python SAST)') {
      steps {
        // รันเป็น root ใน container เพื่อติดตั้งได้แน่นอน
        sh '''
          docker run --rm -u 0:0 \
            -v "$PWD":/ws -w /ws \
            python:3.11-slim \
            sh -lc '
              pip install --no-cache-dir -q bandit && \
              bandit -r . -f sarif -o "$REPORT_DIR/bandit.sarif"
            '
        '''
      }
    }

    stage('pip-audit (Dependencies)') {
      steps {
        // ถ้ามี requirements.txt จะ FAIL เมื่อเจอช่องโหว่
        sh '''
          if [ -f requirements.txt ]; then
            docker run --rm -u 0:0 \
              -v "$PWD":/ws -w /ws \
              python:3.11-slim \
              sh -lc '
                pip install --no-cache-dir -q pip-audit && \
                pip-audit -r requirements.txt --strict -f sarif -o "$REPORT_DIR/pip-audit.sarif"
              '
          else
            # ไม่มี requirements ก็สร้างรายงานว่างไว้ (ไม่ทำให้ล้มที่สเตจนี้)
            echo '{"version":"2.1.0","runs":[]}' > "$REPORT_DIR/pip-audit.sarif"
          fi
        '''
      }
    }

    stage('Trivy FS (Secrets & Misconfig)') {
      steps {
        // ล้มเมื่อเจอ HIGH/CRITICAL และสแกน secret, config, vuln
        sh '''
          docker run --rm \
            -v "$PWD":/ws -w /ws \
            aquasec/trivy:latest fs . \
              --security-checks vuln,secret,config \
              --format sarif \
              --output "$REPORT_DIR/trivy-fs.sarif" \
              --severity HIGH,CRITICAL \
              --exit-code 1
        '''
      }
    }
  }

  post {
    always {
      // เก็บรายงานเสมอ แม้ build จะล้ม
      sh '[ -d "$REPORT_DIR" ] || mkdir -p "$REPORT_DIR"'
      // กันกรณีบางสเตจหยุดก่อนเขียนไฟล์
      sh '[ -f "$REPORT_DIR/semgrep.sarif" ] || echo \'{"version":"2.1.0","runs":[]}\' > "$REPORT_DIR/semgrep.sarif"'
      sh '[ -f "$REPORT_DIR/bandit.sarif" ] || echo \'{"version":"2.1.0","runs":[]}\' > "$REPORT_DIR/bandit.sarif"'
      sh '[ -f "$REPORT_DIR/pip-audit.sarif" ] || echo \'{"version":"2.1.0","runs":[]}\' > "$REPORT_DIR/pip-audit.sarif"'
      sh '[ -f "$REPORT_DIR/trivy-fs.sarif" ] || echo \'{"version":"2.1.0","runs":[]}\' > "$REPORT_DIR/trivy-fs.sarif"'
      archiveArtifacts artifacts: "${REPORT_DIR}/*.sarif", fingerprint: true, allowEmptyArchive: true
      echo "Reports archived in ${REPORT_DIR}/"
    }
    success {
      echo '✅ Build Success (no blocking findings)'
    }
    failure {
      echo '❌ Build Failed due to security findings or scan errors'
    }
  }
}
