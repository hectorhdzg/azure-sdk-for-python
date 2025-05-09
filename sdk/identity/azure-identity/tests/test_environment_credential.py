# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------
import itertools
import os

from azure.identity import CredentialUnavailableError, EnvironmentCredential
from azure.identity._constants import EnvironmentVariables
import pytest

from helpers import mock, GET_TOKEN_METHODS


ALL_VARIABLES = {
    _
    for _ in EnvironmentVariables.CLIENT_SECRET_VARS
    + EnvironmentVariables.CERT_VARS
    + EnvironmentVariables.USERNAME_PASSWORD_VARS
}


@pytest.mark.parametrize("get_token_method", GET_TOKEN_METHODS)
def test_incomplete_configuration(get_token_method):
    """get_token should raise CredentialUnavailableError for incomplete configuration."""

    with mock.patch.dict(os.environ, {}, clear=True):
        with pytest.raises(CredentialUnavailableError) as ex:
            getattr(EnvironmentCredential(), get_token_method)("scope")

    for a, b in itertools.combinations(ALL_VARIABLES, 2):  # all credentials require at least 3 variables set
        with mock.patch.dict(os.environ, {a: "a", b: "b"}, clear=True):
            with pytest.raises(CredentialUnavailableError) as ex:
                getattr(EnvironmentCredential(), get_token_method)("scope")


@pytest.mark.parametrize(
    "credential_name,envvars",
    (
        ("ClientSecretCredential", EnvironmentVariables.CLIENT_SECRET_VARS),
        ("CertificateCredential", EnvironmentVariables.CERT_VARS),
        ("UsernamePasswordCredential", EnvironmentVariables.USERNAME_PASSWORD_VARS),
    ),
)
def test_passes_authority_argument(credential_name, envvars):
    """the credential pass the 'authority' keyword argument to its inner credential"""

    authority = "authority"

    with mock.patch.dict("os.environ", {variable: "foo" for variable in envvars}, clear=True):
        with mock.patch(EnvironmentCredential.__module__ + "." + credential_name) as mock_credential:
            EnvironmentCredential(authority=authority)

    assert mock_credential.call_count == 1
    _, kwargs = mock_credential.call_args
    assert kwargs["authority"] == authority


def test_client_secret_configuration():
    """the credential should pass expected values and any keyword arguments to its inner credential"""

    client_id = "client-id"
    client_secret = "..."
    tenant_id = "tenant_id"
    bar = "bar"

    environment = {
        EnvironmentVariables.AZURE_CLIENT_ID: client_id,
        EnvironmentVariables.AZURE_CLIENT_SECRET: client_secret,
        EnvironmentVariables.AZURE_TENANT_ID: tenant_id,
    }
    with mock.patch(EnvironmentCredential.__module__ + ".ClientSecretCredential") as mock_credential:
        with mock.patch.dict("os.environ", environment, clear=True):
            EnvironmentCredential(foo=bar)

    assert mock_credential.call_count == 1
    _, kwargs = mock_credential.call_args
    assert kwargs["client_id"] == client_id
    assert kwargs["client_secret"] == client_secret
    assert kwargs["tenant_id"] == tenant_id
    assert kwargs["foo"] == bar


def test_certificate_configuration():
    """the credential should pass expected values and any keyword arguments to its inner credential"""

    client_id = "client-id"
    certificate_path = "..."
    tenant_id = "tenant_id"
    bar = "bar"
    send_certificate_chain = "True"

    environment = {
        EnvironmentVariables.AZURE_CLIENT_ID: client_id,
        EnvironmentVariables.AZURE_CLIENT_CERTIFICATE_PATH: certificate_path,
        EnvironmentVariables.AZURE_TENANT_ID: tenant_id,
        EnvironmentVariables.AZURE_CLIENT_SEND_CERTIFICATE_CHAIN: send_certificate_chain,
    }
    with mock.patch(EnvironmentCredential.__module__ + ".CertificateCredential") as mock_credential:
        with mock.patch.dict("os.environ", environment, clear=True):
            EnvironmentCredential(foo=bar)

    assert mock_credential.call_count == 1
    _, kwargs = mock_credential.call_args
    assert kwargs["client_id"] == client_id
    assert kwargs["certificate_path"] == certificate_path
    assert kwargs["tenant_id"] == tenant_id
    assert kwargs["send_certificate_chain"] is True
    assert kwargs["foo"] == bar


def test_certificate_with_password_configuration():
    """the credential should pass expected values and any keyword arguments to its inner credential"""

    client_id = "client-id"
    certificate_path = "..."
    certificate_password = "password"
    tenant_id = "tenant_id"
    bar = "bar"

    environment = {
        EnvironmentVariables.AZURE_CLIENT_ID: client_id,
        EnvironmentVariables.AZURE_CLIENT_CERTIFICATE_PATH: certificate_path,
        EnvironmentVariables.AZURE_CLIENT_CERTIFICATE_PASSWORD: certificate_password,
        EnvironmentVariables.AZURE_TENANT_ID: tenant_id,
    }
    with mock.patch(EnvironmentCredential.__module__ + ".CertificateCredential") as mock_credential:
        with mock.patch.dict("os.environ", environment, clear=True):
            EnvironmentCredential(foo=bar)

    assert mock_credential.call_count == 1
    _, kwargs = mock_credential.call_args
    assert kwargs["client_id"] == client_id
    assert kwargs["certificate_path"] == certificate_path
    assert kwargs["password"] == certificate_password
    assert kwargs["tenant_id"] == tenant_id
    assert kwargs["foo"] == bar


def test_username_password_configuration():
    """the credential should pass expected values and any keyword arguments to its inner credential"""

    client_id = "client-id"
    username = "me@work.com"
    password = "password"
    bar = "bar"

    environment = {
        EnvironmentVariables.AZURE_CLIENT_ID: client_id,
        EnvironmentVariables.AZURE_USERNAME: username,
        EnvironmentVariables.AZURE_PASSWORD: password,
    }
    with mock.patch(EnvironmentCredential.__module__ + ".UsernamePasswordCredential") as mock_credential:
        with mock.patch.dict("os.environ", environment, clear=True):
            EnvironmentCredential(foo=bar)

    assert mock_credential.call_count == 1
    _, kwargs = mock_credential.call_args
    assert kwargs["client_id"] == client_id
    assert kwargs["username"] == username
    assert kwargs["password"] == password
    assert kwargs["foo"] == bar

    # optional tenant id should be used when set
    tenant_id = "tenant-id"
    environment = dict(environment, **{EnvironmentVariables.AZURE_TENANT_ID: tenant_id})
    with mock.patch(EnvironmentCredential.__module__ + ".UsernamePasswordCredential") as mock_credential:
        with mock.patch.dict("os.environ", environment, clear=True):
            EnvironmentCredential(foo=bar)

    assert mock_credential.call_count == 1
    _, kwargs = mock_credential.call_args
    assert kwargs["client_id"] == client_id
    assert kwargs["username"] == username
    assert kwargs["password"] == password
    assert kwargs["tenant_id"] == tenant_id
    assert kwargs["foo"] == bar


def test_username_password_deprecation_warning():
    """the credential should pass expected values and any keyword arguments to its inner credential"""

    client_id = "client-id"
    username = "username"
    password = "password"
    environment = {
        EnvironmentVariables.AZURE_CLIENT_ID: client_id,
        EnvironmentVariables.AZURE_USERNAME: username,
        EnvironmentVariables.AZURE_PASSWORD: password,
    }

    with mock.patch.dict("os.environ", environment, clear=True):
        # the deprecation warning is only raised when the credential is used
        with pytest.deprecated_call():
            EnvironmentCredential()
