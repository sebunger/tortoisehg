#require serve ssl

  $ cat <<EOF >> $HGRCPATH
  > [extensions]
  > tortoisehg.util.hgcommands =
  > EOF

Certificates and server configuration are copied from
mercurial/tests/sslcerts

  $ cat << EOT > priv.pem
  > -----BEGIN RSA PRIVATE KEY-----
  > MIIEpQIBAAKCAQEA2Ugt7jQrD+u+JtIfXZpVepzOAufcX4CMoHV95qZXZml2juGp
  > x3T7wjQPB/IPoOpRG9CoCaekKK+bIqQX1qNuiUa2CsqchNQcua2js5DTttmRYC+f
  > wHaQc0UY1QKe/0r8NFX1XoeIWfuL+0UAERoI1zmhu9px5326C7PoyBPIubT0ejLV
  > LfciFgyHDmqvYGu6cUBpNFrAi8csPNGcyie1Axh0wZ/9jvHdN+iGmaV9GZObGv0G
  > ZpbWlJm8fG+mH1qMFYA6mnknJbEBBTnV0IWdGJalGnz+5GfCvhxzYcEWmLDeO/7F
  > NrWMVT9L8Ky65cygCeJ4lEW1XB1w/6rQYjaSnwIDAQABAoIBAAwDAH8FpUfJCYcN
  > 4KwFByqzFnR0qusgqSWJuT8R/QztUZ+OfBtJrU1MIXSX/iMwMPGvtEpsWRfitVnR
  > 5nt4J3kxTokEMGjrbPca0Uzw+bNHDdFacKNsKookzL2h2nZUh+LAycLDDVekH1Xx
  > t5I6dTiot/cxmVBp0+ontPuylEsnyrQio6eljBfPzxBdRp2lkiymKf3jvbGXRnZ4
  > jSFTRuUlbnVbZ3CKnFPU+d5tvn2nEwU/DVbGpJNZAPl99Q0XUcNF3AtGlwGMvi0X
  > azcIIOn+swLjn+U2S6i3K234ItYS5I+c9Xi+9DO4fuVko+CQ8PWXP2HdAze7DENc
  > zADmd0kCgYEA7nN+qUFAmMOcRE8nSNLt7mcwq6fYQ1MVGikCIXn/PI/wfEqY0lws
  > ZhwykBXog0S7PzYkR3LcDOqN0wDcdJ3K4c/a6Z6IqbXMgxaosYfHCCMtdhy0g0F2
  > ek0SaY3WQhpFRIG19hvB+ZJSc7JQt+TaXeb8HM1452kmOLpfQGiqqTsCgYEA6UXZ
  > bI7c2jO1X+rWF2tZfZdtdeVrIVcm8BunF7ETC4iK/iH2phRQQAh4TFZm6wkX57Tv
  > LKDGxmohFlEK7FOtSCeSSVfkvZYRBuHOYcwBgBr1XzXXjHcMoyr0+LflZysht151
  > 9F0hJwdGQZrivZnv9clJ632RlgE4XlPGskQhRe0CgYEAxVGdhsIQilmUfpJhl8m0
  > SovpoqKKO2wNElDNCpbBt4QFJVU1kR3lP7olvUXj2nyN1okfDGDn52hRZEJaK8ZH
  > lQVDyf7+aDGgwvmFLyOEeB9kB1FJrzQErsAIdICCxMCogUA1KytdIQEMaeEtGn+u
  > k/YIumztl9FTZ64SFGKIlvECgYEA25Kb7csrp1g0yWxKyRCK0+TNa8Pe6ysVw7zD
  > s1FCFAEak8t0Vy+Xui4+zdwmU+XjUn7FAsTzVaBgNJlkJr88xEY7ND4/WRUAQfIa
  > SYO1hdfaTxxnIBiPFKdCnzq5/DplKi0H6lQe+JWoU+hutPlJHZmysq8ncoMDhAZn
  > aTUn/KECgYEAvxGaWt4Fn2tRrHeaG0qT+nMBxd8cTiFInOcYDeS/FlQo3DTDK2Ai
  > qLBa4DinnGN2hSKwnN3R5R2VRxk4I6+ljG0yuNBhJBcAgAFpnHfkuY1maQJB+1xY
  > A07WcM4J3yuPfjcDkipNFQa4Y8oJCaS2yiOPvlUfNQrCLAV+YqHZiiQ=
  > -----END RSA PRIVATE KEY-----
  > EOT

  $ cat << EOT > pub.pem
  > -----BEGIN CERTIFICATE-----
  > MIIDNTCCAh2gAwIBAgIJAJ12yUL2zGhzMA0GCSqGSIb3DQEBCwUAMDExEjAQBgNV
  > BAMMCWxvY2FsaG9zdDEbMBkGCSqGSIb3DQEJARYMaGdAbG9jYWxob3N0MB4XDTE2
  > MDcxMzA0MTcxMloXDTQxMDMwNDA0MTcxMlowMTESMBAGA1UEAwwJbG9jYWxob3N0
  > MRswGQYJKoZIhvcNAQkBFgxoZ0Bsb2NhbGhvc3QwggEiMA0GCSqGSIb3DQEBAQUA
  > A4IBDwAwggEKAoIBAQDZSC3uNCsP674m0h9dmlV6nM4C59xfgIygdX3mpldmaXaO
  > 4anHdPvCNA8H8g+g6lEb0KgJp6Qor5sipBfWo26JRrYKypyE1By5raOzkNO22ZFg
  > L5/AdpBzRRjVAp7/Svw0VfVeh4hZ+4v7RQARGgjXOaG72nHnfboLs+jIE8i5tPR6
  > MtUt9yIWDIcOaq9ga7pxQGk0WsCLxyw80ZzKJ7UDGHTBn/2O8d036IaZpX0Zk5sa
  > /QZmltaUmbx8b6YfWowVgDqaeSclsQEFOdXQhZ0YlqUafP7kZ8K+HHNhwRaYsN47
  > /sU2tYxVP0vwrLrlzKAJ4niURbVcHXD/qtBiNpKfAgMBAAGjUDBOMB0GA1UdDgQW
  > BBT6fA08JcG+SWBN9Y+p575xcFfIVjAfBgNVHSMEGDAWgBT6fA08JcG+SWBN9Y+p
  > 575xcFfIVjAMBgNVHRMEBTADAQH/MA0GCSqGSIb3DQEBCwUAA4IBAQCzJhM/OBoS
  > JXnjfLhZqi6hTmx1XC7MR05z4fWdyBhZx8PwSDEjxAj/omAm2RMEx/Fv1a7FO6hd
  > ClYsxxSfWJO7NQ3V4YLn9AvNr5gcxuXV/4bTtEFNebuzhV06u5nH7pGbHbkxCI+u
  > QekmRTvKIojr8F44cyszEk+MZQ5bFBElByjVzgXNvAaDP0ryUL5eQhLrkuwbNFLQ
  > mFf7EaerMuM28x1knhiH/39s7t92CJgm9+D60TmJ4XXwue1gZ0v9MVS18iOuWyio
  > BklppJsdtDLxHTHGNlBeHdam5VejbXRo7s0y5OfuATwlgcaCMYC/68hVJYwl/GZ7
  > 3YpdNpMshSaE
  > -----END CERTIFICATE-----
  > EOT
  $ cat priv.pem pub.pem >> server.pem
  $ PRIV=`pwd`/server.pem

  $ hg init test
  $ cd test
  $ echo foo>foo
  $ mkdir foo.d foo.d/bAr.hg.d foo.d/baR.d.hg
  $ echo foo>foo.d/foo
  $ echo bar>foo.d/bAr.hg.d/BaR
  $ echo bar>foo.d/baR.d.hg/bAR
  $ hg commit -A -m 1
  adding foo
  adding foo.d/bAr.hg.d/BaR
  adding foo.d/baR.d.hg/bAR
  adding foo.d/foo
  $ hg serve -p $HGPORT -d --pid-file=../hg0.pid --certificate=$PRIV
  $ cat ../hg0.pid >> $DAEMON_PIDS
  $ cd ..

Fingerprints

  $ hg debuggethostfingerprint --insecure https://localhost:$HGPORT/
  sha256:20:de:b3:ad:b4:cd:a5:42:f0:74:41:1c:a2:70:1e:da:6e:c0:5c:16:9e:e7:22:0f:f1:b7:e5:6e:e4:92:af:7e

  $ cat <<EOF >> $HGRCPATH
  > [hostsecurity]
  > localhost:fingerprints = `hg debuggethostfingerprint --insecure https://localhost:$HGPORT/`
  > EOF

  $ hg id https://localhost:$HGPORT/
  8b6053c928fe
