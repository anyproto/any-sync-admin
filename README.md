# any-sync-admin
web admin for edit

> [!WARNING]
> "Show limit" may not be working correctly.

## local development
enable mongo and redis service in docker-compose
```
ln -F -s docker-compose-dev.yml docker-compose.yml
ln -F -s docker-compose-dependences.yml docker-compose.override.yml
```

## run from ghcr.io image
```
ln -F -s docker-compose-ghcr.yml docker-compose.yml
ln -F -s docker-compose-dependences.yml docker-compose.override.yml
```

## make custom config
```
cp example/config.yml etc/config.yml
# edit etc/config.yml
```

## Contribution
Thank you for your desire to develop Anytype together!

❤️ This project and everyone involved in it is governed by the [Code of Conduct](docs/CODE_OF_CONDUCT.md).

🧑‍💻 Check out our [contributing guide](docs/CONTRIBUTING.md) to learn about asking questions, creating issues, or submitting pull requests.

🫢 For security findings, please email [security@anytype.io](mailto:security@anytype.io) and refer to our [security guide](docs/SECURITY.md) for more information.

🤝 Follow us on [Github](https://github.com/anyproto) and join the [Contributors Community](https://github.com/orgs/anyproto/discussions).

---
Made by Any — a Swiss association 🇨🇭

Licensed under [MIT](./LICENSE.md).
