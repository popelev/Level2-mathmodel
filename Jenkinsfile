// Level2-mathmodel Declarative Pipeline — Wave 0 CI skeleton.
// Mirrors Level2 style: dockerized tests/build, ci-* tags, careful post prune.
// Prune ONLY level2-mathmodel*:ci-* — never touch level2-collector / jenkins images.

pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
  }

  parameters {
    booleanParam(name: 'ENABLE_PUSH', defaultValue: false, description: 'Phase 2: push image to registry')
    booleanParam(name: 'ENABLE_DEPLOY', defaultValue: false, description: 'Phase 2: deploy compose on lab VM (main only)')
  }

  environment {
    IMAGE_NAME = 'level2-mathmodel'
    IMAGE_REPO = "${IMAGE_NAME}"
    CI_IMAGE_KEEP = '5'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Engine Test') {
      steps {
        sh '''
          docker run --rm \
            -v "$PWD":/src -w /src \
            python:3.12-bookworm \
            bash -lc '
              set -euo pipefail
              pip install -q -r services/engine/requirements.txt
              cd services/engine
              pytest --junitxml=/src/test-results.xml
            '
        '''
      }
    }

    stage('Web Build') {
      when {
        expression {
          return fileExists('apps/web/package.json')
        }
      }
      steps {
        sh '''
          docker run --rm \
            -v "$PWD/apps/web":/web -w /web \
            node:22-bookworm \
            bash -lc '
              set -euo pipefail
              if [ -f package-lock.json ]; then npm ci; else npm install; fi
              npm run build
            '
        '''
      }
    }

    stage('Docker Build') {
      steps {
        sh '''
          docker build \
            -f deploy/platform/Dockerfile \
            -t "${IMAGE_REPO}:ci-${GIT_COMMIT}" \
            -t "${IMAGE_REPO}:ci-latest" \
            .
        '''
      }
    }

    stage('Push') {
      when {
        allOf {
          expression { return params.ENABLE_PUSH }
          branch 'main'
        }
      }
      steps {
        echo 'Phase 2: configure registry credentials, then docker push ${IMAGE_REPO}:ci-${GIT_COMMIT}'
      }
    }

    stage('Deploy') {
      when {
        allOf {
          expression { return params.ENABLE_DEPLOY }
          branch 'main'
        }
      }
      steps {
        echo 'Phase 2: deploy via deploy/platform/docker-compose.yml on lab host (port 8090, network smoke_default). Never compose-down Level2.'
      }
    }
  }

  post {
    always {
      echo "Finished ${env.GIT_COMMIT} on ${env.BRANCH_NAME}"
      junit allowEmptyResults: true, testResults: 'test-results.xml'
      // Host Docker GC: only level2-mathmodel:ci-* tags. Does not touch
      // level2-collector / jenkins / compose runtime images.
      // POSIX sh only — Jenkins agent uses /bin/sh (dash).
      sh '''
        set -eu
        KEEP="${CI_IMAGE_KEEP:-5}"
        REPO="${IMAGE_REPO:-level2-mathmodel}"
        echo "Pruning ${REPO}:ci-* tags — keep newest ${KEEP} (plus ci-latest)"
        TMP="$(mktemp)"
        docker images --format '{{.CreatedAt}}\t{{.Repository}}:{{.Tag}}\t{{.ID}}' "${REPO}" 2>/dev/null \
          | awk -F'\t' -v p="${REPO}:ci-" '$2 ~ "^"p && $2 !~ /:ci-latest$/ {print}' \
          | sort -r > "$TMP" || true
        n=0
        while IFS= read -r line || [ -n "$line" ]; do
          [ -n "$line" ] || continue
          n=$((n + 1))
          tag=$(printf '%s' "$line" | cut -f2)
          id=$(printf '%s' "$line" | cut -f3)
          if [ "$n" -le "$KEEP" ]; then
            echo "keep ${tag} (${id})"
            continue
          fi
          echo "rm ${tag} (${id})"
          docker rmi "$tag" 2>/dev/null || docker rmi "$id" 2>/dev/null || true
        done < "$TMP"
        rm -f "$TMP"
        # Do NOT run broad docker system prune; only dangling from this prune path.
        docker image prune -f >/dev/null || true
      '''
    }
  }
}
