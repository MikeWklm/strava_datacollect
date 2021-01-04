from setuptools import setup, find_packages

setup(name='strava_datacollect',
      description='analyse your cycling stats',
      author='Mike Winkelmann',
      license='MIT',
      install_requires=['numpy',
                        'pandas',
                        'requests',
                        'hydra-core',
                        'oauthlib',
                        'pytz',
                        'schedule',
                        'requests_oauthlib',
                        'tqdm'
                        ],
      version='0.1.0',
      # list folders, not files
      packages=find_packages(),
      package_data={
          "": ["*.yaml"],
      },
      include_package_data=True,
      entry_points={
          "console_scripts": [
              "strava_collect = strava_datacollect.strava_collect:main",
              "get_auth_url = strava_datacollect.strava_auth:get_auth_url",
              "fetch_token = strava_datacollect.strava_auth:fetch_token",
              "refresh_token = strava_datacollect.strava_auth:refresh_token",
              "init_database = strava_datacollect.strava_query:initialize_database",
              "update_meta = strava_datacollect.strava_query:update_meta",
              "update_raw = strava_datacollect.strava_query:update_raw",
          ]
      }
      )
