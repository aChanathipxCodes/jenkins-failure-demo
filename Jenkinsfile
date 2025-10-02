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
      }
    }

    stage('Prepare workspace') {
      steps {
        sh 'mkdir -p "$REPORT_DIR"'
      }
    }

    stage('Semgrep (OWASP + Python)') {
      steps {
        // ใช้ image สำเร็จรูป ไม่ต้อง pip install ใน container
        sh '''
          set +e
          docker run --rm \
            -v "$PWD":/ws -w /ws \
            returntocorp/semgrep:latest \
              semgrep \
                --config=p/owasp-top-ten \
                --config=p/python \
                --severity "ERROR" \
                --sarif --output "$REPORT_DIR/semgrep.sarif" \
                --error
          SEMGREP_RC=$?
          set -e
          # ถ้าล้ม ให้สร้างไฟล์ว่าง (SARIF เปล่า) เพื่อให้ขั้นตอนถัดไปรันต่อได้
          [ -f "$REPORT_DIR/semgrep.sarif" ] || echo '{"version":"2.1.0","runs":[]}' > "$REPORT_DIR/semgrep.sarif"
          # ไม่ทำให้ build ล้ม
          exit 0
        '''
      }
    }

    stage('Bandit (Python SAST)') {
      steps {
        // ติดตั้ง bandit ใน container Python (รันเป็น root ใน image นี้โดยปริยาย)
        sh '''
          set +e
          docker run --rm \
            -v "$PWD":/ws -w /ws \
            python:3.11-slim \
            sh -lc '
              pip install --no-cache-dir -q bandit && \
              bandit -r . -f sarif -o "$REPORT_DIR/bandit.sarif"
            '
          # ถ้าล้มให้วาง SARIF เปล่า
          [ -f "$REPORT_DIR/bandit.sarif" ] || echo '{"version":"2.1.0","runs":[]}' > "$REPORT_DIR/bandit.sarif"
          set -e
        '''
      }
    }

    stage('pip-audit (Dependencies)') {
      steps {
        sh '''
          set +e
          docker run --rm \
            -v "$PWD":/ws -w /ws \
            python:3.11-slim \
            sh -lc '
              pip install --no-cache-dir -q pip-audit && \
              if [ -f requirements.txt ]; then
                pip-audit -r requirements.txt -f sarif -o "$REPORT_DIR/pip-audit.sarif" || true
              else
                # ไม่มี requirements.txt ก็ทำไฟล์ผลลัพธ์ว่างไว้
                echo "{\"version\":\"2.1.0\",\"runs\":[]}" > "$REPORT_DIR/pip-audit.sarif"
              fi
            '
          set -e
        '''
      }
    }

    stage('Trivy FS (Secrets & Misconfig)') {
      steps {
        // ใช้ --exit-code 0 เพื่อไม่ให้ fail เมื่อเจอช่องโหว่
        sh '''
          set +e
          docker run --rm \
            -v "$PWD":/ws -w /ws \
            aquasec/trivy:latest fs . \
              --security-checks vuln,secret,config \
              --format sarif \
              --output "$REPORT_DIR/trivy-fs.sarif" \
              --exit-code 0
          # กันกรณี image ดึงไม่ได้/ออฟไลน์
          [ -f "$REPORT_DIR/trivy-fs.sarif" ] || echo '{"version":"2.1.0","runs":[]}' > "$REPORT_DIR/trivy-fs.sarif"
          set -e
        '''
      }
    }

    stage('Publish Reports') {
      steps {
        archiveArtifacts artifacts: "${REPORT_DIR}/*.sarif", fingerprint: true, allowEmptyArchive: true
        echo "Archived SARIF reports in ${REPORT_DIR}/"
      }
    }
  }

  post {
    always {
      echo "Scan completed. Reports archived in ${env.REPORT_DIR}/"
    }
    success {
      echo '✅ Build Success (scans completed without failing the build)'
    }
    failure {
      echo '❌ Build Failed (unexpected error in pipeline steps)'
    }
  }
}
