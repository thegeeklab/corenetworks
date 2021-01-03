local PythonVersion(pyversion='3.6') = {
  name: 'python' + std.strReplace(pyversion, '.', '') + '-pytest',
  image: 'python:' + pyversion,
  environment: {
    PY_COLORS: 1,
  },
  commands: [
    'pip install poetry poetry-dynamic-versioning -qq',
    'poetry install -q',
    'poetry run pytest',
    'poetry version',
  ],
  depends_on: [
    'fetch',
  ],
};

local PipelineLint = {
  kind: 'pipeline',
  image_pull_secrets: ['docker_config'],
  name: 'lint',
  platform: {
    os: 'linux',
    arch: 'amd64',
  },
  steps: [
    {
      name: 'yapf',
      image: 'python:3.9',
      environment: {
        PY_COLORS: 1,
      },
      commands: [
        'git fetch -tq',
        'pip install poetry poetry-dynamic-versioning -qq',
        'poetry install -q',
        'poetry run yapf -dr ./corenetworks',
      ],
    },
    {
      name: 'flake8',
      image: 'python:3.9',
      environment: {
        PY_COLORS: 1,
      },
      commands: [
        'git fetch -tq',
        'pip install poetry poetry-dynamic-versioning -qq',
        'poetry install -q',
        'poetry run flake8 ./corenetworks',
      ],
    },
  ],
  trigger: {
    ref: ['refs/heads/main', 'refs/tags/**', 'refs/pull/**'],
  },
};

local PipelineTest = {
  kind: 'pipeline',
  image_pull_secrets: ['docker_config'],
  name: 'test',
  platform: {
    os: 'linux',
    arch: 'amd64',
  },
  steps: [
    {
      name: 'fetch',
      image: 'python:3.9',
      commands: [
        'git fetch -tq',
      ],
    },
    PythonVersion(pyversion='3.6'),
    PythonVersion(pyversion='3.7'),
    PythonVersion(pyversion='3.8'),
    PythonVersion(pyversion='3.9'),
    {
      name: 'codecov',
      image: 'python:3.9',
      environment: {
        PY_COLORS: 1,
        CODECOV_TOKEN: { from_secret: 'codecov_token' },
      },
      commands: [
        'pip install codecov -qq',
        'codecov --required -X gcov',
      ],
      depends_on: [
        'python36-pytest',
        'python37-pytest',
        'python38-pytest',
        'python39-pytest',
      ],
    },
  ],
  depends_on: [
    'lint',
  ],
  trigger: {
    ref: ['refs/heads/main', 'refs/tags/**', 'refs/pull/**'],
  },
};

local PipelineSecurity = {
  kind: 'pipeline',
  image_pull_secrets: ['docker_config'],
  name: 'security',
  platform: {
    os: 'linux',
    arch: 'amd64',
  },
  steps: [
    {
      name: 'bandit',
      image: 'python:3.9',
      environment: {
        PY_COLORS: 1,
      },
      commands: [
        'git fetch -tq',
        'pip install poetry poetry-dynamic-versioning -qq',
        'poetry install -q',
        'poetry run bandit -r ./corenetworks -x ./corenetworks/test',
      ],
    },
  ],
  depends_on: [
    'test',
  ],
  trigger: {
    ref: ['refs/heads/main', 'refs/tags/**', 'refs/pull/**'],
  },
};

local PipelineBuildPackage = {
  kind: 'pipeline',
  image_pull_secrets: ['docker_config'],
  name: 'build-package',
  platform: {
    os: 'linux',
    arch: 'amd64',
  },
  steps: [
    {
      name: 'build',
      image: 'python:3.9',
      environment: {
        SETUPTOOLS_SCM_PRETEND_VERSION: '${DRONE_TAG##v}',
      },
      commands: [
        'git fetch -tq',
        'pip install poetry poetry-dynamic-versioning -qq',
        'poetry build',
      ],
    },
    {
      name: 'checksum',
      image: 'alpine',
      commands: [
        'cd dist/ && sha256sum * > ../sha256sum.txt',
      ],
    },
    {
      name: 'publish-github',
      image: 'plugins/github-release',
      settings: {
        overwrite: true,
        api_key: { from_secret: 'github_token' },
        files: ['dist/*', 'sha256sum.txt'],
        title: '${DRONE_TAG}',
        note: 'CHANGELOG.md',
      },
      when: {
        ref: ['refs/tags/**'],
      },
    },
    {
      name: 'publish-pypi',
      image: 'python:3.9',
      commands: [
        'git fetch -tq',
        'pip install poetry poetry-dynamic-versioning -qq',
        'poetry publish -n',
      ],
      environment: {
        POETRY_HTTP_BASIC_PYPI_USERNAME: { from_secret: 'pypi_username' },
        POETRY_HTTP_BASIC_PYPI_PASSWORD: { from_secret: 'pypi_password' },
      },
      when: {
        ref: ['refs/tags/**'],
      },
    },
  ],
  depends_on: [
    'security',
  ],
  trigger: {
    ref: ['refs/heads/main', 'refs/tags/**', 'refs/pull/**'],
  },
};

local PipelineDocs = {
  kind: 'pipeline',
  image_pull_secrets: ['docker_config'],
  name: 'docs',
  platform: {
    os: 'linux',
    arch: 'amd64',
  },
  concurrency: {
    limit: 1,
  },
  steps: [
    {
      name: 'generate',
      image: 'python:3.9',
      commands: [
        'git fetch -tq',
        'pip install poetry poetry-dynamic-versioning -qq',
        'poetry install',
        'make doc',
      ],
    },
    {
      name: 'markdownlint',
      image: 'thegeeklab/markdownlint-cli',
      commands: [
        "markdownlint 'docs/content/**/*.md' 'README.md' 'CONTRIBUTING.md' -p .gitignore",
      ],
    },
    {
      name: 'spellcheck',
      image: 'node:lts-alpine',
      commands: [
        'npm install -g spellchecker-cli',
        "spellchecker --files 'docs/content/**/*.md' 'README.md' -d .dictionary -p spell indefinite-article syntax-urls --no-suggestions",
      ],
      environment: {
        FORCE_COLOR: true,
        NPM_CONFIG_LOGLEVEL: 'error',
      },
    },
    {
      name: 'testbuild',
      image: 'klakegg/hugo:0.80.0-ext-alpine-ci',
      commands: [
        'hugo-official -s docs/ -b http://localhost/',
      ],
    },
    {
      name: 'link-validation',
      image: 'thegeeklab/link-validator',
      commands: [
        'link-validator -ro',
      ],
      environment: {
        LINK_VALIDATOR_BASE_DIR: 'docs/public',
      },
    },
    {
      name: 'build',
      image: 'klakegg/hugo:0.80.0-ext-alpine-ci',
      commands: [
        'hugo-official -s docs/',
      ],
    },
    {
      name: 'beautify',
      image: 'node:lts-alpine',
      commands: [
        'npm install -g js-beautify',
        "html-beautify -r -f 'docs/public/**/*.html'",
      ],
      environment: {
        FORCE_COLOR: true,
        NPM_CONFIG_LOGLEVEL: 'error',
      },
    },
    {
      name: 'publish',
      image: 'plugins/s3-sync',
      settings: {
        access_key: { from_secret: 's3_access_key' },
        bucket: 'geekdocs',
        delete: true,
        endpoint: 'https://sp.rknet.org',
        path_style: true,
        secret_key: { from_secret: 's3_secret_access_key' },
        source: 'docs/public/',
        strip_prefix: 'docs/public/',
        target: '/${DRONE_REPO_NAME}',
      },
      when: {
        ref: ['refs/heads/main', 'refs/tags/**'],
      },
    },
  ],
  depends_on: [
    'build-package',
  ],
  trigger: {
    ref: ['refs/heads/main', 'refs/tags/**', 'refs/pull/**'],
  },
};

local PipelineNotifications = {
  kind: 'pipeline',
  image_pull_secrets: ['docker_config'],
  name: 'notifications',
  platform: {
    os: 'linux',
    arch: 'amd64',
  },
  steps: [
    {
      name: 'matrix',
      image: 'plugins/matrix',
      settings: {
        homeserver: { from_secret: 'matrix_homeserver' },
        roomid: { from_secret: 'matrix_roomid' },
        template: 'Status: **{{ build.status }}**<br/> Build: [{{ repo.Owner }}/{{ repo.Name }}]({{ build.link }}) ({{ build.branch }}) by {{ build.author }}<br/> Message: {{ build.message }}',
        username: { from_secret: 'matrix_username' },
        password: { from_secret: 'matrix_password' },
      },
      when: {
        status: ['success', 'failure'],
      },
    },
  ],
  depends_on: [
    'docs',
  ],
  trigger: {
    ref: ['refs/heads/main', 'refs/tags/**'],
    status: ['success', 'failure'],
  },
};

[
  PipelineLint,
  PipelineTest,
  PipelineSecurity,
  PipelineBuildPackage,
  PipelineDocs,
  PipelineNotifications,
]
