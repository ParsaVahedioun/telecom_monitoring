# SNMP Usage Monitoring Project — Code Audit (V1.3)

## Directory Tree

```
  telecom_monitoring/
    .gitattributes
    app.py
    base.py
    collector.py
    config.py
    data.db
    database.py
    init_db.py
    models.py
    .git/
      COMMIT_EDITMSG
      FETCH_HEAD
      HEAD
      config
      description
      index
      hooks/
        applypatch-msg.sample
        commit-msg.sample
        fsmonitor-watchman.sample
        post-update.sample
        pre-applypatch.sample
        pre-commit.sample
        pre-merge-commit.sample
        pre-push.sample
        pre-rebase.sample
        pre-receive.sample
        prepare-commit-msg.sample
        push-to-checkout.sample
        sendemail-validate.sample
        update.sample
      info/
        exclude
      logs/
        HEAD
        refs/
          heads/
            main
          remotes/
            origin/
              HEAD
              main
      objects/
        02/
          f96d9642953cf44d870f67dae76328e3a3da51
        03/
          4e848032092eaf8ef96eac731b6ed5961987f3
        05/
          1771cec5ad788f26850ab278034af0e0749bd8
          f9ff496c8bccdf96bcd50fb76593b79f4449fc
        10/
          5ce2da2d6447d11dfe32bfb846c3d5b199fc99
        1d/
          3ce46ba0d13183e3244cba5b930b5e27be4c6b
          7a0ea6da002bb4419d7e977c128b292d08eea6
        26/
          d33521af10bcc7fd8cea344038eaaeb78d0ef5
        2d/
          14e351d4ff6fcbec793862f13af0e8f35d9760
        31/
          91cab423cabb48272872f06b448194a04132be
        38/
          a6681a2345f650a052707d704918c4164c9e0a
        39/
          594eec9eb824226686ce1f4fa054a8291c96b9
        3f/
          697933679e3257f4d760d6a44c6acd0378c011
        42/
          633856ab9c72c3b18afcb278719083d9afe611
        54/
          b42d89fde2d91ea8664eaf20a01b0361eb3db4
        57/
          972c8629f895968b71557a63b04c491ef37c01
        5b/
          e4f7b0f06a914c0a5c4808c96410556e3af449
        61/
          270d4423c19abcab6db1d39f31ac37e5f796df
        65/
          d19cc5e663580096da8aa087639e588042616b
        6f/
          00cc9dc0bfd3f6a69fd90b110515afb0c39f4f
        77/
          b66dc4be8ddba7b2efd9aba24c1868893815da
        7c/
          25dc1bf4bf85b4c558f8bcabb8d4b7a584a37b
        7d/
          9b07547a93045d6d910711fb6e9de58ca6dea0
        87/
          b85372f562113e25e8b8a18dff99af188e634f
        94/
          a25f7f4cb416c083d265558da75d457237d671
        97/
          824ec9b0149e48c91dce4fee530335b327c686
        a2/
          76d2288c41fe9278c11630e9f8edd572344c1d
        a9/
          05158836d62a22bb7d76ccff025912b7a58507
        af/
          df61c68c5b6aa19dadf200513509017c8fd219
        b2/
          74c239411c510ab2803be1802464790b08e5b9
        b4/
          db8934c3290c9e915c0c3800e46c427c02e561
        b5/
          41672368c4ed78043091e129a2084c1a3aeaa6
        b7/
          5d13f209c97b5310fb90fdcf5f3d0db5a6621e
        ba/
          54c6a2f7b6cb3b92e4080e94b22663a8a221b0
        bc/
          2e262575db7efe5b2588ddc02d620c8de7c7d5
        c6/
          4a5c11da97f4b8cc23538dc5be3a7db9896d41
        d8/
          b3f6cbf0c04e3481a87fcd0d588f490d9fdac7
        dd/
          22de7a446126c9676ee109501c67b3577b12f1
        df/
          e0770424b2a19faf507a501ebfc23be8f54e7b
        e3/
          29d2c9756f35187b8f505a105261a39f39d4eb
        e5/
          55972738f8eb7300208a3d807a27a35dfa8f25
        e6/
          9de29bb2d1d6434b8b29ae775ad8c2e48c5391
        f4/
          3d78d5f81daecccbcc0adfd68346350290c544
        f6/
          1eedf5f55de4aa00d01808388105f4569a7d13
        f7/
          503e8d30bc83de8ae3b1de75962f27d5c87182
        f8/
          64ecff7978a591eabe3ac5ca18ecafd8062c58
        info/
        pack/
      refs/
        heads/
          main
        remotes/
          origin/
            HEAD
            main
        tags/
    .idea/
      .gitignore
      misc.xml
      modules.xml
      telecom_monitoring.iml
      vcs.xml
      workspace.xml
      inspectionProfiles/
        profiles_settings.xml
    api/
      main.py
      schemas.py
      routes/
        admin_routes.py
        routes.py
        user.py
        __pycache__/
          admin_routes.cpython-313.pyc
          routes.cpython-313.pyc
          user.cpython-313.pyc
      __pycache__/
        main.cpython-313.pyc
        routes.cpython-313.pyc
        schemas.cpython-313.pyc
    telecom_dashboard/
      app.js
      index.html
      style.css
      admin/
        add-user.html
        index.html
        user-list.html
    __pycache__/
      app.cpython-313.pyc
      base.cpython-313.pyc
      collector.cpython-313.pyc
      config.cpython-313.pyc
      database.cpython-313.pyc
      models.cpython-313.pyc
```

## Key Files Scanned

- README.md
- api/main.py
- base.py
- collector.py
- config.py
- database.py
- models.py
- requirements.txt
- telecom_monitoring/api/main.py
- telecom_monitoring/api/routes/admin_routes.py
- telecom_monitoring/api/routes/routes.py
- telecom_monitoring/api/routes/user.py
- telecom_monitoring/api/schemas.py
- telecom_monitoring/telecom_dashboard/admin/add-user.html
- telecom_monitoring/telecom_dashboard/admin/index.html
- telecom_monitoring/telecom_dashboard/admin/user-list.html
- telecom_monitoring/telecom_dashboard/app.js
- telecom_monitoring/telecom_dashboard/index.html
- telecom_monitoring/telecom_dashboard/style.css

## SQLAlchemy Models

_No models.py found or parse failed._

## FastAPI Endpoints

- `GET` /  _(in telecom_monitoring/api/main.py)_
- `GET` /admin  _(in telecom_monitoring/api/main.py)_
- `GET` /api/live-speed  _(in telecom_monitoring/api/routes/routes.py)_
- `GET` /api/traffic-stats  _(in telecom_monitoring/api/routes/routes.py)_
- `GET` /traffic  _(in telecom_monitoring/api/routes/routes.py)_
- `GET` /user  _(in telecom_monitoring/api/main.py)_
- `GET` /user-list  _(in telecom_monitoring/api/main.py)_
- `GET` /users/summary  _(in telecom_monitoring/api/routes/admin_routes.py)_
- `GET` /users/{user_id}/traffic  _(in telecom_monitoring/api/routes/routes.py)_

## SNMP OIDs Detected

_No explicit numeric OIDs found._

## Potential Issues / TODOs

- [ ] No major issues detected.