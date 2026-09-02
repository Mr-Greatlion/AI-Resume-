"""
Pydantic models for the review form (POST /review) + the extracted-vs-reviewed diff.
Field names are camelCase to match the AVR frontend / v1 API contract.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app_v2.constants import FIELD_KEYS


class EmailItem(BaseModel):
    emailAddress: str = Field(..., max_length=120)
    isPrimary: bool = False

    @field_validator("emailAddress")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.fullmatch(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", v):
            raise ValueError(f"invalid email: {v}")
        return v


class PhoneItem(BaseModel):
    countryCode: str = Field("+91", max_length=6)
    mobileNumber: str = Field(..., max_length=20)
    isPrimary: bool = False

    @field_validator("countryCode")
    @classmethod
    def _cc(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith("+"):
            v = "+" + v
        if not re.fullmatch(r"\+\d{1,4}", v):
            raise ValueError(f"invalid country code: {v}")
        return v

    @field_validator("mobileNumber")
    @classmethod
    def _num(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if not 6 <= len(digits) <= 15:
            raise ValueError(f"invalid mobile number: {v}")
        return digits


class CertificateItem(BaseModel):
    name: str = Field("", max_length=200)
    fileId: Optional[str] = None
    fileName: Optional[str] = None


class LocationItem(BaseModel):
    country: str = Field("", max_length=80)
    state: str = Field("", max_length=80)
    city: str = Field("", max_length=80)


class AddressItem(BaseModel):
    address: str = Field("", max_length=400)
    city: str = Field("", max_length=80)
    state: str = Field("", max_length=80)
    country: str = Field("", max_length=80)
    pinCode: str = Field("", max_length=12)


class ReviewedFields(BaseModel):
    """Exactly what the Review & Edit column holds when the reviewer presses submit."""
    fullName: str = Field(..., min_length=1, max_length=120)
    surname: str = Field("", max_length=80)
    emails: list[EmailItem] = Field(..., min_length=1)
    mobileNumbers: list[PhoneItem] = Field(default_factory=list)
    jobTitle: str = Field(..., min_length=1, max_length=120)
    yearsOfExperience: str = Field("", max_length=30)
    educationQualification: str = Field("", max_length=80)
    certificates: list[CertificateItem] = Field(default_factory=list)
    currentWorkLocation: LocationItem = Field(default_factory=LocationItem)
    permanentAddress: AddressItem = Field(default_factory=AddressItem)
    pan: str = Field("", max_length=12)
    aadhar: str = Field("", max_length=14)

    @field_validator("fullName", "surname", "jobTitle", "yearsOfExperience", "educationQualification")
    @classmethod
    def _strip(cls, v: str) -> str:
        return re.sub(r"\s+", " ", v or "").strip()

    @field_validator("pan")
    @classmethod
    def _pan(cls, v: str) -> str:
        v = (v or "").strip().upper()
        if v and not re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", v):
            raise ValueError("PAN must look like ABCDE1234F")
        return v

    @field_validator("aadhar")
    @classmethod
    def _aadhar(cls, v: str) -> str:
        v = re.sub(r"\D", "", v or "")
        if v and len(v) != 12:
            raise ValueError("Aadhaar must be 12 digits")
        return v

    @model_validator(mode="after")
    def _primary_flags(self):
        if self.emails and not any(e.isPrimary for e in self.emails):
            self.emails[0].isPrimary = True
        if self.mobileNumbers and not any(p.isPrimary for p in self.mobileNumbers):
            self.mobileNumbers[0].isPrimary = True
        if not self.permanentAddress.country:
            self.permanentAddress.country = self.currentWorkLocation.country or "India"
        return self


class ReviewSubmit(BaseModel):
    uid: str = Field(..., min_length=8, max_length=40)
    fields: ReviewedFields
    reviewer: Optional[str] = Field(None, max_length=120)
    notes: Optional[str] = Field(None, max_length=1000)


# ── diff helpers ─────────────────────────────────────────────────────────────

def _norm(v: Any) -> Any:
    """Normalise a value so cosmetic differences don't count as a correction."""
    if isinstance(v, str):
        return re.sub(r"\s+", " ", v).strip().lower()
    if isinstance(v, list):
        out = []
        for item in v:
            if isinstance(item, dict):
                d = {k: _norm(x) for k, x in item.items() if k not in ("isPrimary", "fileId", "fileName")}
                out.append(tuple(sorted(d.items())))
            else:
                out.append(_norm(item))
        return sorted(out, key=str)
    if isinstance(v, dict):
        return {k: _norm(x) for k, x in v.items()}
    return v


def build_corrections(extracted: dict, reviewed: dict) -> tuple[dict, int, int]:
    """
    extracted: {key: descriptor}   reviewed: {key: plain value}
    Returns (corrections, total, changed) where corrections[key] =
      {"extracted": ..., "reviewed": ..., "changed": bool, "extractedStatus": ..., "action": ...}
    action ∈ confirmed | corrected | filled | cleared
    """
    corrections: dict = {}
    changed = 0
    for key in FIELD_KEYS:
        desc = extracted.get(key) or {}
        ext_val = desc.get("value", "")
        rev_val = reviewed.get(key, "")
        same = _norm(ext_val) == _norm(rev_val)
        ext_empty = _norm(ext_val) in ("", [], {}, None) or (isinstance(ext_val, dict) and not any(_norm(ext_val).values()))
        rev_empty = _norm(rev_val) in ("", [], {}, None) or (isinstance(rev_val, dict) and not any(_norm(rev_val).values()))
        if same:
            action = "confirmed"
        elif ext_empty and not rev_empty:
            action = "filled"
        elif rev_empty and not ext_empty:
            action = "cleared"
        else:
            action = "corrected"
        if not same:
            changed += 1
        corrections[key] = {
            "extracted": ext_val, "reviewed": rev_val, "changed": not same,
            "extractedStatus": desc.get("status", "not_extracted"),
            "extractedConfidence": desc.get("confidence", 0), "action": action,
        }
    return corrections, len(FIELD_KEYS), changed
