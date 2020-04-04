local PythonVersion(pyversion='2.7') = {
  name: 'python' + std.strReplace(pyversion, '.', ''),
  image: 'python:' + pyversion,
  environment: {
    PY_COLORS: 1,
  },
  commands: [
    'pip install -r test-requirements.txt -qq',
    'pip install -qq .',
    'pytest --cov=corenetworks/ --no-cov-on-fail',
  ],
  depends_on: [
    'clone',
  ],
};

local PipelineLint = {
  kind: 'pipeline',
  name: 'lint',
  platform: {
    os: 'linux',
    arch: 'amd64',
  },
  steps: [
    {
      name: 'flake8',
      image: 'python:3.8',
      environment: {
        PY_COLORS: 1,
      },
      commands: [
        'pip install -r test-requirements.txt -qq',
        'pip install -qq .',
        'flake8 ./corenetworks',
      ],
    },
  ],
  trigger: {
    ref: ['refs/heads/master', 'refs/tags/**', 'refs/pull/**'],
  },
};

local PipelineTest = {
  kind: 'pipeline',
  name: 'test',
  platform: {
    os: 'linux',
    arch: 'amd64',
  },
  steps: [
    PythonVersion(pyversion='2.7'),
    PythonVersion(pyversion='3.5'),
    PythonVersion(pyversion='3.6'),
    PythonVersion(pyversion='3.7'),
    PythonVersion(pyversion='3.8'),
    {
      name: 'codecov',
      image: 'python:3.8',
      environment: {
        PY_COLORS: 1,
        CODECOV_TOKEN: { from_secret: 'codecov_token' },
      },
      commands: [
        'pip install codecov',
        'codecov --required',
      ],
      depends_on: [
        'python27',
        'python35',
        'python36',
        'python37',
        'python38',
      ],
    },
  ],
  depends_on: [
    'lint',
  ],
  trigger: {
    ref: ['refs/heads/master', 'refs/tags/**', 'refs/pull/**'],
  },
};

local PipelineSecurity = {
  kind: 'pipeline',
  name: 'security',
  platform: {
    os: 'linux',
    arch: 'amd64',
  },
  steps: [
    {
      name: 'bandit',
      image: 'python:3.8',
      environment: {
        PY_COLORS: 1,
      },
      commands: [
        'pip install -r test-requirements.txt -qq',
        'pip install -qq .',
        'bandit -r ./corenetworks -x ./corenetworks/tests',
      ],
    },
  ],
  depends_on: [
    'test',
  ],
  trigger: {
    ref: ['refs/heads/master', 'refs/tags/**', 'refs/pull/**'],
  },
};

local PipelineBuildPackage = {
  kind: 'pipeline',
  name: 'build-package',
  platform: {
    os: 'linux',
    arch: 'amd64',
  },
  steps: [
    {
      name: 'build',
      image: 'python:3.8',
      environment: {
        SETUPTOOLS_SCM_PRETEND_VERSION: '${DRONE_TAG##v}',
      },
      commands: [
        'python setup.py sdist bdist_wheel',
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
      image: 'plugins/pypi',
      settings: {
        username: { from_secret: 'pypi_username' },
        password: { from_secret: 'pypi_password' },
        repository: 'https://upload.pypi.org/legacy/',
        skip_build: true,
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
    ref: ['refs/heads/master', 'refs/tags/**', 'refs/pull/**'],
  },
};

local PipelineDocs = {
  kind: 'pipeline',
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
      name: 'assets',
      image: 'byrnedo/alpine-curl',
      commands: [
        'mkdir -p docs/themes/hugo-geekdoc/',
        'curl -L https://github.com/xoxys/hugo-geekdoc/releases/latest/download/hugo-geekdoc.tar.gz | tar -xz -C docs/themes/hugo-geekdoc/ --strip-components=1',
      ],
    },
    {
      name: 'test',
      image: 'klakegg/hugo:0.59.1-ext-alpine',
      commands: [
        'cd docs/ && hugo-official',
      ],
    },
    {
      name: 'freeze',
      image: 'appleboy/drone-ssh:1.5.5',
      settings: {
        host: { from_secret: 'ssh_host' },
        key: { from_secret: 'ssh_key' },
        script: [
          'cp -R /var/www/virtual/geeklab/html/corenetworks.geekdocs.de/ /var/www/virtual/geeklab/html/corenetworks_freeze/',
          'ln -sfn /var/www/virtual/geeklab/html/corenetworks_freeze /var/www/virtual/geeklab/corenetworks.geekdocs.de',
        ],
        username: { from_secret: 'ssh_username' },
      },
    },
    {
      name: 'publish',
      image: 'appleboy/drone-scp',
      settings: {
        host: { from_secret: 'ssh_host' },
        key: { from_secret: 'ssh_key' },
        rm: true,
        source: 'docs/public/*',
        strip_components: 2,
        target: '/var/www/virtual/geeklab/html/corenetworks.geekdocs.de/',
        username: { from_secret: 'ssh_username' },
      },
    },
    {
      name: 'cleanup',
      image: 'appleboy/drone-ssh:1.5.5',
      settings: {
        host: { from_secret: 'ssh_host' },
        key: { from_secret: 'ssh_key' },
        script: [
          'ln -sfn /var/www/virtual/geeklab/html/corenetworks.geekdocs.de /var/www/virtual/geeklab/corenetworks.geekdocs.de',
          'rm -rf /var/www/virtual/geeklab/html/corenetworks_freeze/',
        ],
        username: { from_secret: 'ssh_username' },
      },
    },
  ],
  depends_on: [
    'build-package',
  ],
  trigger: {
    ref: ['refs/heads/master', 'refs/tags/**'],
  },
};

local PipelineNotifications = {
  kind: 'pipeline',
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
    ref: ['refs/heads/master', 'refs/tags/**'],
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
