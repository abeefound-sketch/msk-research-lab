"""OpenSSL EVP AES-256-GCM Authenticated Encryption with Associated Data (AEAD).

Provides NIST SP 800-38D standard-aligned hardware-accelerated AES-256-GCM via standard libcrypto
without requiring external third-party binary wheels, with graceful fallback.
Note: Standard OS libcrypto runs the default non-FIPS cryptographic provider unless explicitly
configured with an external FIPS 140 provider module.
"""

import ctypes
import ctypes.util
import os
import sys
from typing import Any, Dict, Optional, Tuple


class OpenSSLCryptoError(Exception):
    """Base error for OpenSSL crypto operations."""
    pass


class OpenSSLAuthTagMismatch(OpenSSLCryptoError):
    """Raised when GMAC tag authentication fails during decryption."""
    pass


_libcrypto: Optional[ctypes.CDLL] = None
_libcrypto_initialized: bool = False

# OpenSSL constants
EVP_CTRL_GCM_SET_IVLEN = 0x9
EVP_CTRL_GCM_GET_TAG = 0x10
EVP_CTRL_GCM_SET_TAG = 0x11


def _load_libcrypto() -> Optional[ctypes.CDLL]:
    """Attempt to load system OpenSSL libcrypto dynamically across platforms."""
    global _libcrypto, _libcrypto_initialized
    if _libcrypto_initialized:
        return _libcrypto

    _libcrypto_initialized = True

    search_names = []
    found_name = ctypes.util.find_library("crypto")
    if found_name:
        search_names.append(found_name)

    if sys.platform.startswith("linux"):
        search_names.extend(["libcrypto.so.3", "libcrypto.so.1.1", "libcrypto.so"])
    elif sys.platform == "win32":
        search_names.extend([
            "libcrypto-3-x64.dll",
            "libcrypto-1_1-x64.dll",
            "libcrypto.dll",
            r"C:\Windows\System32\libcrypto-3-x64.dll",
        ])
    elif sys.platform == "darwin":
        search_names.extend(["libcrypto.3.dylib", "libcrypto.dylib"])

    for name in search_names:
        try:
            lib = ctypes.CDLL(name)
            # Verify required EVP functions exist
            if hasattr(lib, "EVP_aes_256_gcm") and hasattr(lib, "EVP_CIPHER_CTX_new"):
                # Configure function signatures for 64-bit safety
                lib.EVP_CIPHER_CTX_new.restype = ctypes.c_void_p
                lib.EVP_CIPHER_CTX_free.argtypes = [ctypes.c_void_p]
                lib.EVP_CIPHER_CTX_free.restype = None

                lib.EVP_aes_256_gcm.restype = ctypes.c_void_p

                lib.EVP_EncryptInit_ex.argtypes = [
                    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                    ctypes.c_char_p, ctypes.c_char_p
                ]
                lib.EVP_EncryptInit_ex.restype = ctypes.c_int

                lib.EVP_EncryptUpdate.argtypes = [
                    ctypes.c_void_p, ctypes.c_void_p,
                    ctypes.POINTER(ctypes.c_int), ctypes.c_char_p, ctypes.c_int
                ]
                lib.EVP_EncryptUpdate.restype = ctypes.c_int

                lib.EVP_EncryptFinal_ex.argtypes = [
                    ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)
                ]
                lib.EVP_EncryptFinal_ex.restype = ctypes.c_int

                lib.EVP_DecryptInit_ex.argtypes = [
                    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                    ctypes.c_char_p, ctypes.c_char_p
                ]
                lib.EVP_DecryptInit_ex.restype = ctypes.c_int

                lib.EVP_DecryptUpdate.argtypes = [
                    ctypes.c_void_p, ctypes.c_void_p,
                    ctypes.POINTER(ctypes.c_int), ctypes.c_char_p, ctypes.c_int
                ]
                lib.EVP_DecryptUpdate.restype = ctypes.c_int

                lib.EVP_DecryptFinal_ex.argtypes = [
                    ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)
                ]
                lib.EVP_DecryptFinal_ex.restype = ctypes.c_int

                lib.EVP_CIPHER_CTX_ctrl.argtypes = [
                    ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_void_p
                ]
                lib.EVP_CIPHER_CTX_ctrl.restype = ctypes.c_int

                _libcrypto = lib
                return _libcrypto
        except Exception:
            continue

    return None


def is_openssl_gcm_available() -> bool:
    """Return True if system OpenSSL EVP AES-256-GCM is operational."""
    return _load_libcrypto() is not None


def probe_fips_status() -> Dict[str, Any]:
    """Probe whether the underlying OpenSSL libcrypto has CMVP FIPS provider active.
    
    Standard Linux/Windows system libcrypto distributions use the default (non-FIPS) provider.
    This function accurately reports whether FIPS mode is enabled via EVP_default_properties_is_fips_enabled
    or FIPS_mode to avoid false compliance claims (DEF-20).
    """
    lib = _load_libcrypto()
    if not lib:
        return {
            "openssl_available": False,
            "is_fips": False,
            "provider": "NONE",
            "standard": "NIST_SP_800_38D",
            "compliance_claim": "NON_FIPS_FALLBACK"
        }

    is_fips = False
    provider_name = "default"

    if hasattr(lib, "EVP_default_properties_is_fips_enabled"):
        try:
            lib.EVP_default_properties_is_fips_enabled.argtypes = [ctypes.c_void_p]
            lib.EVP_default_properties_is_fips_enabled.restype = ctypes.c_int
            is_fips = bool(lib.EVP_default_properties_is_fips_enabled(None))
            if is_fips:
                provider_name = "fips"
        except Exception:
            pass
    elif hasattr(lib, "FIPS_mode"):
        try:
            lib.FIPS_mode.argtypes = []
            lib.FIPS_mode.restype = ctypes.c_int
            is_fips = bool(lib.FIPS_mode())
            if is_fips:
                provider_name = "fips"
        except Exception:
            pass

    return {
        "openssl_available": True,
        "is_fips": is_fips,
        "provider": provider_name,
        "standard": "NIST_SP_800_38D",
        "compliance_claim": "NIST_SP_800_38D_ALIGNED_DEFAULT_PROVIDER" if not is_fips else "FIPS_140_ACTIVE"
    }


def aes_256_gcm_encrypt(
    key: bytes,
    iv: bytes,
    plaintext: bytes,
    aad: bytes = b"",
) -> Tuple[bytes, bytes]:
    """Encrypt plaintext using AES-256-GCM authenticated encryption.
    
    Args:
        key: 32-byte (256-bit) symmetric key.
        iv: 12-byte (96-bit) cryptographically random nonce.
        plaintext: Arbitrary byte payload to encrypt.
        aad: Optional authenticated associated data verified by GMAC tag.
        
    Returns:
        Tuple of (ciphertext, 16-byte authentication tag).
    """
    if len(key) != 32:
        raise OpenSSLCryptoError(f"AES-256 requires 32-byte key, got {len(key)} bytes.")
    if len(iv) != 12:
        raise OpenSSLCryptoError(f"Standard GCM requires 12-byte IV, got {len(iv)} bytes.")

    lib = _load_libcrypto()
    if not lib:
        raise OpenSSLCryptoError("OpenSSL libcrypto is unavailable on this host.")

    ctx = lib.EVP_CIPHER_CTX_new()
    if not ctx:
        raise OpenSSLCryptoError("Failed to initialize OpenSSL EVP cipher context.")

    try:
        # 1. Initialize cipher
        if lib.EVP_EncryptInit_ex(ctx, lib.EVP_aes_256_gcm(), None, None, None) != 1:
            raise OpenSSLCryptoError("EVP_EncryptInit_ex failed to set cipher.")

        # 2. Set IV length (12 bytes)
        if lib.EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_IVLEN, len(iv), None) != 1:
            raise OpenSSLCryptoError("Failed to set GCM IV length.")

        # 3. Bind key and IV
        if lib.EVP_EncryptInit_ex(ctx, None, None, key, iv) != 1:
            raise OpenSSLCryptoError("Failed to bind key and IV to cipher context.")

        # 4. Process AAD (Associated Authenticated Data) if present
        if aad:
            dummy_len = ctypes.c_int(0)
            if lib.EVP_EncryptUpdate(ctx, None, ctypes.byref(dummy_len), aad, len(aad)) != 1:
                raise OpenSSLCryptoError("Failed to process GCM AAD.")

        # 5. Encrypt payload
        out_buf = ctypes.create_string_buffer(len(plaintext) + 16)
        out_len = ctypes.c_int(0)
        if len(plaintext) > 0:
            if lib.EVP_EncryptUpdate(ctx, ctypes.byref(out_buf), ctypes.byref(out_len), plaintext, len(plaintext)) != 1:
                raise OpenSSLCryptoError("EVP_EncryptUpdate failed during encryption.")

        enc_len = out_len.value

        # 6. Finalize encryption
        final_len = ctypes.c_int(0)
        if lib.EVP_EncryptFinal_ex(ctx, ctypes.byref(out_buf, enc_len), ctypes.byref(final_len)) != 1:
            raise OpenSSLCryptoError("EVP_EncryptFinal_ex failed.")

        total_enc = enc_len + final_len.value

        # 7. Extract 16-byte GMAC authentication tag
        tag_buf = ctypes.create_string_buffer(16)
        if lib.EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, 16, tag_buf) != 1:
            raise OpenSSLCryptoError("Failed to extract GCM authentication tag.")

        ciphertext = out_buf.raw[:total_enc]
        tag = tag_buf.raw[:16]
        return ciphertext, tag

    finally:
        lib.EVP_CIPHER_CTX_free(ctx)


def aes_256_gcm_decrypt(
    key: bytes,
    iv: bytes,
    ciphertext: bytes,
    tag: bytes,
    aad: bytes = b"",
) -> bytes:
    """Decrypt ciphertext and authenticate integrity using AES-256-GCM.
    
    Fails closed: if the GMAC tag does not match, raises OpenSSLAuthTagMismatch
    immediately before returning any unauthenticated plaintext.
    """
    if len(key) != 32:
        raise OpenSSLCryptoError(f"AES-256 requires 32-byte key, got {len(key)} bytes.")
    if len(iv) != 12:
        raise OpenSSLCryptoError(f"Standard GCM requires 12-byte IV, got {len(iv)} bytes.")
    if len(tag) != 16:
        raise OpenSSLCryptoError(f"Standard GCM tag requires 16 bytes, got {len(tag)} bytes.")

    lib = _load_libcrypto()
    if not lib:
        raise OpenSSLCryptoError("OpenSSL libcrypto is unavailable on this host.")

    ctx = lib.EVP_CIPHER_CTX_new()
    if not ctx:
        raise OpenSSLCryptoError("Failed to initialize OpenSSL EVP cipher context.")

    try:
        # 1. Initialize cipher
        if lib.EVP_DecryptInit_ex(ctx, lib.EVP_aes_256_gcm(), None, None, None) != 1:
            raise OpenSSLCryptoError("EVP_DecryptInit_ex failed to set cipher.")

        # 2. Set IV length
        if lib.EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_IVLEN, len(iv), None) != 1:
            raise OpenSSLCryptoError("Failed to set GCM IV length.")

        # 3. Bind key and IV
        if lib.EVP_DecryptInit_ex(ctx, None, None, key, iv) != 1:
            raise OpenSSLCryptoError("Failed to bind key and IV.")

        # 4. Process AAD
        if aad:
            dummy_len = ctypes.c_int(0)
            if lib.EVP_DecryptUpdate(ctx, None, ctypes.byref(dummy_len), aad, len(aad)) != 1:
                raise OpenSSLCryptoError("Failed to process GCM AAD.")

        # 5. Decrypt payload
        dec_buf = ctypes.create_string_buffer(len(ciphertext) + 16)
        dec_len = ctypes.c_int(0)
        if len(ciphertext) > 0:
            if lib.EVP_DecryptUpdate(ctx, ctypes.byref(dec_buf), ctypes.byref(dec_len), ciphertext, len(ciphertext)) != 1:
                raise OpenSSLCryptoError("EVP_DecryptUpdate failed.")

        total_dec = dec_len.value

        # 6. Set expected tag for hardware GMAC verification
        if lib.EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, 16, tag) != 1:
            raise OpenSSLCryptoError("Failed to set expected GCM tag.")

        # 7. Finalize and verify tag
        final_len = ctypes.c_int(0)
        ret = lib.EVP_DecryptFinal_ex(ctx, ctypes.byref(dec_buf, total_dec), ctypes.byref(final_len))
        if ret <= 0:
            raise OpenSSLAuthTagMismatch(
                "AEAD Authentication Failed: ciphertext corrupted or passphrase incorrect."
            )

        total_dec += final_len.value
        return dec_buf.raw[:total_dec]

    finally:
        lib.EVP_CIPHER_CTX_free(ctx)
