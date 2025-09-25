# Changelog

## [0.5.1](https://github.com/flowcore-io/speedlocal-streamlit/compare/v0.5.0...v0.5.1) (2025-09-25)


### Bug Fixes

* **helm:** :rocket: Update timesApp tag to v0.5.0 ([91a2f48](https://github.com/flowcore-io/speedlocal-streamlit/commit/91a2f4821bb9a63c1f7a8b413976c16db98b616a))
* **times_app:** :sparkles: Update page title in TIMES Data Explorer ([752845e](https://github.com/flowcore-io/speedlocal-streamlit/commit/752845ebc25fd6c75f246f57c172251cbc1de211))

## [0.5.0](https://github.com/flowcore-io/speedlocal-streamlit/compare/v0.4.1...v0.5.0) (2025-09-25)


### Features

* **helm:** :sparkles: Add multiple Streamlit apps with updated configurations ([b194b55](https://github.com/flowcore-io/speedlocal-streamlit/commit/b194b5581f843703b1bb7e861a760e4b81542023))


### Bug Fixes

* **docs:** :sparkles: Update project structure to single-app Streamlit architecture and add TIMES app migration documentation ([b6e40c2](https://github.com/flowcore-io/speedlocal-streamlit/commit/b6e40c26c06b1a61b21b0941ed4cde207ce8c709))
* **helm:** :rocket: Update all app tags to v0.4.1 ([c965f8d](https://github.com/flowcore-io/speedlocal-streamlit/commit/c965f8de7b272efd7dbb8570ad6b683ae0707ddd))

## [0.4.1](https://github.com/flowcore-io/speedlocal-streamlit/compare/v0.4.0...v0.4.1) (2025-09-25)


### Bug Fixes

* **docker:** :art: Update Dockerfile to use public ECR Python image ([818deff](https://github.com/flowcore-io/speedlocal-streamlit/commit/818deffca792c5efd68f03ece6f8ffb314dc6907))

## [0.4.0](https://github.com/flowcore-io/speedlocal-streamlit/compare/v0.3.0...v0.4.0) (2025-09-24)


### Features

* **docs:** :sparkles: Add comprehensive multi-app deployment and CI/CD validation documentation ([1cd1224](https://github.com/flowcore-io/speedlocal-streamlit/commit/1cd12249a95e1fef58331782fbd5f4843fa64fe6))


### Bug Fixes

* **helm:** :rocket: Update prod tag to v0.3.0 ([945d240](https://github.com/flowcore-io/speedlocal-streamlit/commit/945d24097672a138b6640c025f100380eb84aa48))
* pin exact package versions to resolve pybind11 conflicts in multi-page app ([e438948](https://github.com/flowcore-io/speedlocal-streamlit/commit/e438948c2cd6ee95ff90719fc9d5c69ffaee7c01))

## [0.3.0](https://github.com/flowcore-io/speedlocal-streamlit/compare/v0.2.3...v0.3.0) (2025-09-24)


### Features

* add comprehensive multi-page analytics with TIMES data explorer, energy flow maps, Sankey diagrams, and database tools ([418ab5c](https://github.com/flowcore-io/speedlocal-streamlit/commit/418ab5cd86e1a272e7b8f57a83f8031f3210d155))


### Bug Fixes

* **helm:** :rocket: Update prod tag to v0.2.3 ([3500c5e](https://github.com/flowcore-io/speedlocal-streamlit/commit/3500c5ea647d45a0db5f845d77956f2485f5438d))

## [0.2.3](https://github.com/flowcore-io/speedlocal-streamlit/compare/v0.2.2...v0.2.3) (2025-09-24)


### Bug Fixes

* **helm:** :sparkles: Add Chart.lock and new Helm chart dependencies for flowcore-microservices and flowcore-secret-requester ([be26f7a](https://github.com/flowcore-io/speedlocal-streamlit/commit/be26f7a8cfe8da533e2a9c677af01165a2a9c84b))

## [0.2.2](https://github.com/flowcore-io/speedlocal-streamlit/compare/v0.2.1...v0.2.2) (2025-09-24)


### Bug Fixes

* **workflows:** :art: Update production values path in streamlit-cicd workflow ([7572262](https://github.com/flowcore-io/speedlocal-streamlit/commit/757226229fe5061ba104b3f6fe38e2837a45975c))

## [0.2.1](https://github.com/flowcore-io/speedlocal-streamlit/compare/v0.2.0...v0.2.1) (2025-09-24)


### Bug Fixes

* **docker:** :art: Force re-deploy ([d3c7c83](https://github.com/flowcore-io/speedlocal-streamlit/commit/d3c7c831a5bb052c8d51b57602cdb91a03e1aaef))
* **helm:** :art: Correct indentation in values.yaml for route configuration ([5edee13](https://github.com/flowcore-io/speedlocal-streamlit/commit/5edee136c2b53ff1422d66aed4c8b04dab3741c9))
* **helm:** :rocket: Update prod tag to v0.2.0 ([cff5707](https://github.com/flowcore-io/speedlocal-streamlit/commit/cff5707c3036117f5225edb0106301e2e32a8e2f))
* move production.yaml to configuration/ directory for ArgoCD compatibility ([d0ede9c](https://github.com/flowcore-io/speedlocal-streamlit/commit/d0ede9c010c1948417084af85ee531470b1aaba7))
* **workflows:** :sparkles: Add input for manual tag in streamlit-cicd workflow ([360aed5](https://github.com/flowcore-io/speedlocal-streamlit/commit/360aed5ca199a04e53ac25f2bcaaa54f13db1f5d))

## [0.2.0](https://github.com/flowcore-io/speedlocal-streamlit/compare/v0.1.0...v0.2.0) (2025-09-23)


### Features

* initial Streamlit scaffold for Speed Local ([185ee1d](https://github.com/flowcore-io/speedlocal-streamlit/commit/185ee1d719d3924b05ba502af33048425c527bb1))


### Bug Fixes

* **workflows:** :art: Add empty line for readability in streamlit-cicd workflow ([50a4671](https://github.com/flowcore-io/speedlocal-streamlit/commit/50a46710f73de406714ee461fc83dc4f32c33889))
* **workflows:** :art: Simplify paths in release-please workflow configuration ([6202b11](https://github.com/flowcore-io/speedlocal-streamlit/commit/6202b11d080e26abf48b11f9ac6ffe02991d2896))
* **workflows:** :art: Update paths in release-please configuration files for consistency ([35e03bb](https://github.com/flowcore-io/speedlocal-streamlit/commit/35e03bbbf686e3066505c3740e5748b65e05d195))
* **workflows:** :bug: Update GitHub token in release-please workflow for security ([5836feb](https://github.com/flowcore-io/speedlocal-streamlit/commit/5836feb9c544ff3cceebdbbac9a7e815ae59b3d2))
* **workflows:** :bug: Update paths in release-please workflow configuration ([3fb06f3](https://github.com/flowcore-io/speedlocal-streamlit/commit/3fb06f3785320074217a82060749bf97f8f96ea1))
* **workflows:** :sparkles: Add CI/CD workflows for Streamlit app deployment and release management ([c0f7c1f](https://github.com/flowcore-io/speedlocal-streamlit/commit/c0f7c1fe0df074804bc172c937cb4a0423cc2df7))
* **workflows:** :sparkles: Add release-please configuration and manifest files for automated versioning ([f093f02](https://github.com/flowcore-io/speedlocal-streamlit/commit/f093f02f2a388ce33231efc29119f8eb7740811f))

## 1.0.0 (2025-09-23)


### Features

* initial Streamlit scaffold for Speed Local ([185ee1d](https://github.com/flowcore-io/speedlocal-streamlit/commit/185ee1d719d3924b05ba502af33048425c527bb1))


### Bug Fixes

* **workflows:** :sparkles: Add CI/CD workflows for Streamlit app deployment and release management ([c0f7c1f](https://github.com/flowcore-io/speedlocal-streamlit/commit/c0f7c1fe0df074804bc172c937cb4a0423cc2df7))
