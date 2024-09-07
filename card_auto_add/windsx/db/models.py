from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ACL(Base):
    __tablename__ = 'ACL'

    ID: Mapped[int] = mapped_column('ID')
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    Acl: Mapped[int] = mapped_column('Acl', primary_key=True)
    Tz: Mapped[int] = mapped_column('Tz', primary_key=True)
    DGrp: Mapped[int] = mapped_column('DGrp', primary_key=True)
    DlFlag: Mapped[int] = mapped_column('DlFlag')
    CkSum: Mapped[int] = mapped_column('CkSum')


class CameraName(Base):
    __tablename__ = 'CameraName'

    ID: Mapped[int] = mapped_column('ID')
    Loc: Mapped[int] = mapped_column('Loc', primary_key=True)
    Name: Mapped[str] = mapped_column('Name', primary_key=True)
    Icon1: Mapped[int] = mapped_column('Icon1')
    ListOrder: Mapped[int] = mapped_column('ListOrder')
    Notes: Mapped[str] = mapped_column('Notes')
    IOID: Mapped[int] = mapped_column('IOID')
    CamType: Mapped[int] = mapped_column('CamType')
    SvrName: Mapped[str] = mapped_column('SvrName')
    CamSel: Mapped[str] = mapped_column('CamSel')
    PTZ: Mapped[bool] = mapped_column('PTZ')
    Hist: Mapped[int] = mapped_column('Hist')
    PreSet: Mapped[int] = mapped_column('PreSet')
    DvrUser: Mapped[str] = mapped_column('DvrUser')
    DvrPw: Mapped[str] = mapped_column('DvrPw')


class CommSvr(Base):
    __tablename__ = 'CommSvr'

    ID: Mapped[int] = mapped_column('ID')
    Name: Mapped[str] = mapped_column('Name')
    WorkSta: Mapped[int] = mapped_column('WorkSta', primary_key=True)
    IPAddress: Mapped[str] = mapped_column('IPAddress')
    IPName: Mapped[str] = mapped_column('IPName')
    Throttle: Mapped[int] = mapped_column('Throttle')
    SaveDBEdits: Mapped[bool] = mapped_column('SaveDBEdits')
    BuCsAddress: Mapped[str] = mapped_column('BuCsAddress')
    EKey: Mapped[str] = mapped_column('EKey')


class DataBaseInfo(Base):
    __tablename__ = 'DataBaseInfo'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    DataBaseVersion: Mapped[int] = mapped_column('DataBaseVersion')
    LastBackUp: Mapped[DateTime] = mapped_column('LastBackUp')
    Opr: Mapped[int] = mapped_column('Opr')
    InstallDate: Mapped[DateTime] = mapped_column('InstallDate')
    Register: Mapped[bool] = mapped_column('Register')
    SmContract: Mapped[bool] = mapped_column('SmContract')
    ContractDate: Mapped[DateTime] = mapped_column('ContractDate')
    ServiceCode: Mapped[str] = mapped_column('ServiceCode')
    Opc: Mapped[str] = mapped_column('Opc')


class EmailGrpName(Base):
    __tablename__ = 'EmailGrpName'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp')
    Name: Mapped[str] = mapped_column('Name')
    Notes: Mapped[str] = mapped_column('Notes')


class IO(Base):
    __tablename__ = 'IO'

    ID: Mapped[int] = mapped_column('ID')
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    Device: Mapped[int] = mapped_column('Device', primary_key=True)
    IO: Mapped[int] = mapped_column('IO', primary_key=True)
    Type: Mapped[str] = mapped_column('Type', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    T1: Mapped[int] = mapped_column('T1')
    T2: Mapped[int] = mapped_column('T2')
    T3: Mapped[int] = mapped_column('T3')
    T4: Mapped[int] = mapped_column('T4')
    AbortDelay: Mapped[int] = mapped_column('AbortDelay')
    Ogrp: Mapped[int] = mapped_column('Ogrp')
    LinkStatus: Mapped[str] = mapped_column('LinkStatus')
    ActionMsg: Mapped[int] = mapped_column('ActionMsg')
    ReportChg: Mapped[bool] = mapped_column('ReportChg')
    AlarmPri: Mapped[int] = mapped_column('AlarmPri')
    CircuitType: Mapped[int] = mapped_column('CircuitType')
    StatusPort: Mapped[int] = mapped_column('StatusPort')
    NormMsg: Mapped[int] = mapped_column('NormMsg')
    AbnormMsg: Mapped[int] = mapped_column('AbnormMsg')
    AlarmPort: Mapped[int] = mapped_column('AlarmPort')
    AlarmMsg: Mapped[int] = mapped_column('AlarmMsg')
    RestorMsg: Mapped[int] = mapped_column('RestorMsg')
    ReportFlag: Mapped[bool] = mapped_column('ReportFlag')
    FailSecure: Mapped[bool] = mapped_column('FailSecure')
    OpenName: Mapped[str] = mapped_column('OpenName')
    SecuName: Mapped[str] = mapped_column('SecuName')
    LinkState: Mapped[str] = mapped_column('LinkState')
    WireTag: Mapped[str] = mapped_column('WireTag')
    Icon1: Mapped[int] = mapped_column('Icon1')
    Icon2: Mapped[int] = mapped_column('Icon2')
    AlarmWav: Mapped[int] = mapped_column('AlarmWav')
    DlFlag: Mapped[int] = mapped_column('DlFlag')
    Notes: Mapped[str] = mapped_column('Notes')
    AlarmMap: Mapped[bool] = mapped_column('AlarmMap')
    AlarmResolve: Mapped[bool] = mapped_column('AlarmResolve')
    AlarmEcho: Mapped[bool] = mapped_column('AlarmEcho')
    ListOrder: Mapped[int] = mapped_column('ListOrder')
    ReqComment: Mapped[bool] = mapped_column('ReqComment')
    CameraID: Mapped[int] = mapped_column('CameraID')
    AlarmCam: Mapped[bool] = mapped_column('AlarmCam')
    ElevDev: Mapped[int] = mapped_column('ElevDev')
    AlarmEmail: Mapped[int] = mapped_column('AlarmEmail')


class Icons(Base):
    __tablename__ = 'Icons'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    FileName: Mapped[str] = mapped_column('FileName')


class ImageSrcName(Base):
    __tablename__ = 'ImageSrcName'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    FileExt: Mapped[str] = mapped_column('FileExt')
    QFactor: Mapped[int] = mapped_column('QFactor')
    SrcType: Mapped[int] = mapped_column('SrcType')
    CommPort: Mapped[int] = mapped_column('CommPort')
    Notes: Mapped[str] = mapped_column('Notes')


class ImageSrc(Base):
    __tablename__ = 'ImageSrc'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    SourceID: Mapped[int] = mapped_column('SourceID', ForeignKey('ImageSrcName.ID'))
    WorkSta: Mapped[int] = mapped_column('WorkSta')
    ExecOrder: Mapped[int] = mapped_column('ExecOrder')
    CmdType: Mapped[str] = mapped_column('CmdType')
    CmdString: Mapped[str] = mapped_column('CmdString')


class LocGrp(Base):
    __tablename__ = 'LocGrp'

    ID: Mapped[int] = mapped_column('ID')
    LocGrp: Mapped[int] = mapped_column('LocGrp', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    NDigits: Mapped[int] = mapped_column('NDigits')
    DupPin: Mapped[bool] = mapped_column('DupPin')
    HexCodes: Mapped[bool] = mapped_column('HexCodes')
    AsciiCodes: Mapped[bool] = mapped_column('AsciiCodes')
    WsPrintingNames: Mapped[str] = mapped_column('WsPrintingNames')
    TimePrintStarted: Mapped[DateTime] = mapped_column('TimePrintStarted')


class AclGrpName(Base):
    __tablename__ = 'AclGrpName'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'))
    Name: Mapped[str] = mapped_column('Name')
    Notes: Mapped[str] = mapped_column('Notes')
    Visitor: Mapped[bool] = mapped_column('Visitor')
    IsMaster: Mapped[bool] = mapped_column('IsMaster')


class AclGrpCombo(Base):
    __tablename__ = 'AclGrpCombo'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    AclGrpNameID: Mapped[int] = mapped_column('AclGrpNameID', ForeignKey('AclGrpName.ID'))
    ComboID: Mapped[int] = mapped_column('ComboID')
    LocGrp: Mapped[int] = mapped_column('LocGrp')


class BdgName(Base):
    __tablename__ = 'BdgName'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'))
    Name: Mapped[str] = mapped_column('Name')
    XSize: Mapped[int] = mapped_column('XSize')
    YSize: Mapped[int] = mapped_column('YSize')
    XOffSet: Mapped[int] = mapped_column('XOffSet')
    YOffSet: Mapped[int] = mapped_column('YOffSet')
    MagStripe1: Mapped[str] = mapped_column('MagStripe1')
    MagStripe2: Mapped[str] = mapped_column('MagStripe2')
    MagStripe3: Mapped[str] = mapped_column('MagStripe3')
    BdgType: Mapped[int] = mapped_column('BdgType')
    FilterIndex: Mapped[int] = mapped_column('FilterIndex')
    Notes: Mapped[str] = mapped_column('Notes')


class Badge(Base):
    __tablename__ = 'Badge'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    BadgeID: Mapped[int] = mapped_column('BadgeID', ForeignKey('BdgName.ID'))
    ZOrder: Mapped[int] = mapped_column('ZOrder')
    FieldType: Mapped[str] = mapped_column('FieldType')
    Name: Mapped[str] = mapped_column('Name')
    XPos: Mapped[int] = mapped_column('XPos')
    YPos: Mapped[int] = mapped_column('YPos')
    XSize: Mapped[int] = mapped_column('XSize')
    YSize: Mapped[int] = mapped_column('YSize')
    Center: Mapped[bool] = mapped_column('Center')
    Shrink2Fit: Mapped[bool] = mapped_column('Shrink2Fit')
    BarCode: Mapped[bool] = mapped_column('BarCode')
    BcFormat: Mapped[str] = mapped_column('BcFormat')
    Aspect: Mapped[bool] = mapped_column('Aspect')
    ChromaKey: Mapped[bool] = mapped_column('ChromaKey')
    MagSTrack: Mapped[int] = mapped_column('MagSTrack')
    MaxChars: Mapped[int] = mapped_column('MaxChars')
    Rotation: Mapped[int] = mapped_column('Rotation')
    RGB: Mapped[int] = mapped_column('RGB')
    FName: Mapped[str] = mapped_column('FName')
    FSize: Mapped[int] = mapped_column('FSize')
    FBold: Mapped[bool] = mapped_column('FBold')
    FItalic: Mapped[bool] = mapped_column('FItalic')
    FUnderLine: Mapped[bool] = mapped_column('FUnderLine')
    TexRecXPos: Mapped[int] = mapped_column('TexRecXPos')
    TexRecYPos: Mapped[int] = mapped_column('TexRecYPos')
    TexRecXSize: Mapped[int] = mapped_column('TexRecXSize')
    TexRecYSize: Mapped[int] = mapped_column('TexRecYSize')
    Ghost: Mapped[int] = mapped_column('Ghost')


class CARDS(Base):
    __tablename__ = 'CARDS'

    ID: Mapped[int] = mapped_column('ID')
    NameID: Mapped[int] = mapped_column('NameID')
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), primary_key=True)
    Code: Mapped[float] = mapped_column('Code', primary_key=True)
    Pin: Mapped[int] = mapped_column('Pin')
    StartDate: Mapped[DateTime] = mapped_column('StartDate')
    StopDate: Mapped[DateTime] = mapped_column('StopDate')
    Status: Mapped[bool] = mapped_column('Status')
    CardNum: Mapped[str] = mapped_column('CardNum')
    GTour: Mapped[bool] = mapped_column('GTour')
    NumUses: Mapped[int] = mapped_column('NumUses')
    Notes: Mapped[str] = mapped_column('Notes')
    DlFlag: Mapped[int] = mapped_column('DlFlag')
    AclGrpComboID: Mapped[int] = mapped_column('AclGrpComboID')
    APB: Mapped[bool] = mapped_column('APB')
    TempAclGrpComboID: Mapped[int] = mapped_column('TempAclGrpComboID')
    AclStartDate: Mapped[DateTime] = mapped_column('AclStartDate')
    AclStopDate: Mapped[DateTime] = mapped_column('AclStopDate')
    TempAcl: Mapped[bool] = mapped_column('TempAcl')


class COMPANY(Base):
    __tablename__ = 'COMPANY'

    ID: Mapped[int] = mapped_column('ID')
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), primary_key=True)
    Company: Mapped[int] = mapped_column('Company', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    Phone: Mapped[str] = mapped_column('Phone')
    Fax: Mapped[str] = mapped_column('Fax')
    Contact: Mapped[str] = mapped_column('Contact')
    Suite: Mapped[str] = mapped_column('Suite')
    Badge: Mapped[int] = mapped_column('Badge')
    Notes: Mapped[str] = mapped_column('Notes')
    NoUseDays: Mapped[int] = mapped_column('NoUseDays')


class GtsName(Base):
    __tablename__ = 'GtsName'

    ID: Mapped[int] = mapped_column('ID')
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), primary_key=True)
    GtsNum: Mapped[int] = mapped_column('GtsNum', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    Random: Mapped[bool] = mapped_column('Random')
    Notes: Mapped[str] = mapped_column('Notes')
    StartTime: Mapped[DateTime] = mapped_column('StartTime')
    CurrentStation: Mapped[int] = mapped_column('CurrentStation')
    LastStationTime: Mapped[DateTime] = mapped_column('LastStationTime')
    IsPaused: Mapped[bool] = mapped_column('IsPaused')


class GTS(Base):
    __tablename__ = 'GTS'

    ID: Mapped[int] = mapped_column('ID')
    LocGrp: Mapped[int] = mapped_column('LocGrp', primary_key=True)
    GtsNum: Mapped[int] = mapped_column('GtsNum', primary_key=True)
    StaNum: Mapped[int] = mapped_column('StaNum', primary_key=True)
    PointID: Mapped[int] = mapped_column('PointID')
    PointType: Mapped[str] = mapped_column('PointType')
    Event: Mapped[int] = mapped_column('Event')
    MinTime: Mapped[int] = mapped_column('MinTime')
    MaxTime: Mapped[int] = mapped_column('MaxTime')
    ActionMsg: Mapped[int] = mapped_column('ActionMsg')


class HistRptName(Base):
    __tablename__ = 'HistRptName'

    ID: Mapped[int] = mapped_column('ID')
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), primary_key=True)
    Name: Mapped[str] = mapped_column('Name', primary_key=True)
    StartDateOffSet: Mapped[int] = mapped_column('StartDateOffSet')
    StopDateOffSet: Mapped[int] = mapped_column('StopDateOffSet')
    StartTime: Mapped[int] = mapped_column('StartTime')
    StopTime: Mapped[int] = mapped_column('StopTime')
    DailyStartStop: Mapped[bool] = mapped_column('DailyStartStop')
    AllEvn: Mapped[bool] = mapped_column('AllEvn')
    AllDev: Mapped[bool] = mapped_column('AllDev')
    AllNames: Mapped[bool] = mapped_column('AllNames')
    TNA: Mapped[bool] = mapped_column('TNA')
    SortByTime: Mapped[bool] = mapped_column('SortByTime')
    Uses: Mapped[bool] = mapped_column('Uses')
    NameSort: Mapped[bool] = mapped_column('NameSort')
    Summary: Mapped[bool] = mapped_column('Summary')
    Notes: Mapped[str] = mapped_column('Notes')
    DispCodes: Mapped[bool] = mapped_column('DispCodes')
    Elevator: Mapped[bool] = mapped_column('Elevator')


class HistRptDetail(Base):
    __tablename__ = 'HistRptDetail'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    RptID: Mapped[int] = mapped_column('RptID', ForeignKey('HistRptName.ID'))
    Detail: Mapped[str] = mapped_column('Detail')
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'))
    Device: Mapped[int] = mapped_column('Device')
    IO: Mapped[int] = mapped_column('IO')


class ImageType(Base):
    __tablename__ = 'ImageType'

    ID: Mapped[int] = mapped_column('ID')
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), primary_key=True)
    Num: Mapped[int] = mapped_column('Num', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    Source: Mapped[int] = mapped_column('Source')
    DefaultImage: Mapped[bool] = mapped_column('DefaultImage')
    GrayScale: Mapped[bool] = mapped_column('GrayScale')
    CapOrder: Mapped[int] = mapped_column('CapOrder')
    Notes: Mapped[str] = mapped_column('Notes')


class LOC(Base):
    __tablename__ = 'LOC'

    ID: Mapped[int] = mapped_column('ID')
    Loc: Mapped[int] = mapped_column('Loc', primary_key=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'))
    Name: Mapped[str] = mapped_column('Name')
    Address: Mapped[str] = mapped_column('Address')
    City: Mapped[str] = mapped_column('City')
    State: Mapped[str] = mapped_column('State')
    Zip: Mapped[str] = mapped_column('Zip')
    Status: Mapped[bool] = mapped_column('Status')
    PlFlag: Mapped[bool] = mapped_column('PlFlag')
    FullDlFlag: Mapped[bool] = mapped_column('FullDlFlag')
    LoFlag: Mapped[bool] = mapped_column('LoFlag')
    PlTime: Mapped[DateTime] = mapped_column('PlTime')
    DelayPl: Mapped[int] = mapped_column('DelayPl')
    AfterHoursPl: Mapped[bool] = mapped_column('AfterHoursPl')
    LocPw: Mapped[str] = mapped_column('LocPw')
    ConnType: Mapped[str] = mapped_column('ConnType')
    Phone: Mapped[str] = mapped_column('Phone')
    PcPhone: Mapped[str] = mapped_column('PcPhone')
    CheckTime: Mapped[int] = mapped_column('CheckTime')
    LogRepEn: Mapped[bool] = mapped_column('LogRepEn')
    DevRepEn: Mapped[bool] = mapped_column('DevRepEn')
    MastIsDev: Mapped[bool] = mapped_column('MastIsDev')
    LinkEn: Mapped[bool] = mapped_column('LinkEn')
    OllEn: Mapped[bool] = mapped_column('OllEn')
    AntiPassEn: Mapped[bool] = mapped_column('AntiPassEn')
    CrWithKp: Mapped[bool] = mapped_column('CrWithKp')
    DeniedsAl: Mapped[int] = mapped_column('DeniedsAl')
    WeigNoise: Mapped[bool] = mapped_column('WeigNoise')
    DBadCard: Mapped[bool] = mapped_column('DBadCard')
    AlResAk: Mapped[bool] = mapped_column('AlResAk')
    AutoForgive: Mapped[bool] = mapped_column('AutoForgive')
    MissFail: Mapped[int] = mapped_column('MissFail')
    HoursDiff: Mapped[int] = mapped_column('HoursDiff')
    ActionMsg: Mapped[int] = mapped_column('ActionMsg')
    LastComm: Mapped[DateTime] = mapped_column('LastComm')
    CommErr: Mapped[int] = mapped_column('CommErr')
    NodeCs: Mapped[int] = mapped_column('NodeCs')
    OGrpCs: Mapped[int] = mapped_column('OGrpCs')
    HolCs: Mapped[int] = mapped_column('HolCs')
    FacilCs: Mapped[int] = mapped_column('FacilCs')
    OllCs: Mapped[int] = mapped_column('OllCs')
    TzCs: Mapped[int] = mapped_column('TzCs')
    AclCs: Mapped[int] = mapped_column('AclCs')
    DGrpCs: Mapped[int] = mapped_column('DGrpCs')
    CodeCs: Mapped[int] = mapped_column('CodeCs')
    DlFlag: Mapped[int] = mapped_column('DlFlag')
    RAM: Mapped[int] = mapped_column('RAM')
    FwVersion: Mapped[int] = mapped_column('FwVersion')
    FwDate: Mapped[DateTime] = mapped_column('FwDate')
    CpuType: Mapped[int] = mapped_column('CpuType')
    IoType: Mapped[int] = mapped_column('IoType')
    Notes: Mapped[str] = mapped_column('Notes')
    EchoLoc: Mapped[int] = mapped_column('EchoLoc')
    AlarmEcho: Mapped[bool] = mapped_column('AlarmEcho')
    RemotePC: Mapped[bool] = mapped_column('RemotePC')
    ModemAlarm: Mapped[int] = mapped_column('ModemAlarm')
    SaveLastDev: Mapped[bool] = mapped_column('SaveLastDev')
    TimeZone: Mapped[str] = mapped_column('TimeZone')
    DST: Mapped[bool] = mapped_column('DST')
    AlarmEmail: Mapped[int] = mapped_column('AlarmEmail')
    EKey: Mapped[str] = mapped_column('EKey')


class AclGrp(Base):
    __tablename__ = 'AclGrp'

    ID: Mapped[int] = mapped_column('ID')
    AclGrpNameID: Mapped[int] = mapped_column('AclGrpNameID', ForeignKey('AclGrpName.ID'), primary_key=True)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    Dev: Mapped[int] = mapped_column('Dev', primary_key=True)
    Tz1: Mapped[int] = mapped_column('Tz1')
    Tz2: Mapped[int] = mapped_column('Tz2')
    Tz3: Mapped[int] = mapped_column('Tz3')
    Tz4: Mapped[int] = mapped_column('Tz4')


class AclName(Base):
    __tablename__ = 'AclName'

    ID: Mapped[int] = mapped_column('ID')
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    Acl: Mapped[int] = mapped_column('Acl', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    Notes: Mapped[str] = mapped_column('Notes')
    Visitor: Mapped[bool] = mapped_column('Visitor')
    AclGrpComboID: Mapped[int] = mapped_column('AclGrpComboID')
    LastUse: Mapped[DateTime] = mapped_column('LastUse')


class DEV(Base):
    __tablename__ = 'DEV'

    ID: Mapped[int] = mapped_column('ID')
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    Device: Mapped[int] = mapped_column('Device', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    Type: Mapped[str] = mapped_column('Type')
    OpenTime: Mapped[int] = mapped_column('OpenTime')
    TooLong: Mapped[int] = mapped_column('TooLong')
    TimedATPB: Mapped[int] = mapped_column('TimedATPB')
    Oll: Mapped[bool] = mapped_column('Oll')
    Lnk2Out1: Mapped[bool] = mapped_column('Lnk2Out1')
    ReverseData: Mapped[bool] = mapped_column('ReverseData')
    DoorInputs: Mapped[bool] = mapped_column('DoorInputs')
    DodRelock: Mapped[bool] = mapped_column('DodRelock')
    Trace: Mapped[bool] = mapped_column('Trace')
    ExitUnlock: Mapped[bool] = mapped_column('ExitUnlock')
    LogExitReq: Mapped[bool] = mapped_column('LogExitReq')
    DelayUnlock: Mapped[bool] = mapped_column('DelayUnlock')
    KpTz1: Mapped[int] = mapped_column('KpTz1')
    KpTz2: Mapped[int] = mapped_column('KpTz2')
    CrTz1: Mapped[int] = mapped_column('CrTz1')
    CrTz2: Mapped[int] = mapped_column('CrTz2')
    IrTz1: Mapped[int] = mapped_column('IrTz1')
    IrTz2: Mapped[int] = mapped_column('IrTz2')
    AntiPass1: Mapped[int] = mapped_column('AntiPass1')
    AntiPass2: Mapped[int] = mapped_column('AntiPass2')
    AntiPass3: Mapped[int] = mapped_column('AntiPass3')
    AntiPass4: Mapped[int] = mapped_column('AntiPass4')
    ActionMsg: Mapped[int] = mapped_column('ActionMsg')
    DeniedMsg: Mapped[int] = mapped_column('DeniedMsg')
    TNA: Mapped[str] = mapped_column('TNA')
    WireTag: Mapped[str] = mapped_column('WireTag')
    DlFlag: Mapped[int] = mapped_column('DlFlag')
    Enabled: Mapped[bool] = mapped_column('Enabled')
    RAM: Mapped[int] = mapped_column('RAM')
    FwVersion: Mapped[int] = mapped_column('FwVersion')
    FwDate: Mapped[DateTime] = mapped_column('FwDate')
    CpuType: Mapped[int] = mapped_column('CpuType')
    IoType: Mapped[int] = mapped_column('IoType')
    LowAC: Mapped[bool] = mapped_column('LowAC')
    HighAC: Mapped[bool] = mapped_column('HighAC')
    LowBattery: Mapped[bool] = mapped_column('LowBattery')
    Notes: Mapped[str] = mapped_column('Notes')
    AlarmEcho: Mapped[bool] = mapped_column('AlarmEcho')
    CkSum: Mapped[int] = mapped_column('CkSum')
    DisAbleCode: Mapped[bool] = mapped_column('DisAbleCode')
    AlarmEmail: Mapped[int] = mapped_column('AlarmEmail')


class DGRP(Base):
    __tablename__ = 'DGRP'

    ID: Mapped[int] = mapped_column('ID')
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    DGrp: Mapped[int] = mapped_column('DGrp', primary_key=True)
    DlFlag: Mapped[int] = mapped_column('DlFlag')
    D0: Mapped[bool] = mapped_column('D0')
    D1: Mapped[bool] = mapped_column('D1')
    D2: Mapped[bool] = mapped_column('D2')
    D3: Mapped[bool] = mapped_column('D3')
    D4: Mapped[bool] = mapped_column('D4')
    D5: Mapped[bool] = mapped_column('D5')
    D6: Mapped[bool] = mapped_column('D6')
    D7: Mapped[bool] = mapped_column('D7')
    D8: Mapped[bool] = mapped_column('D8')
    D9: Mapped[bool] = mapped_column('D9')
    D10: Mapped[bool] = mapped_column('D10')
    D11: Mapped[bool] = mapped_column('D11')
    D12: Mapped[bool] = mapped_column('D12')
    D13: Mapped[bool] = mapped_column('D13')
    D14: Mapped[bool] = mapped_column('D14')
    D15: Mapped[bool] = mapped_column('D15')
    D16: Mapped[bool] = mapped_column('D16')
    D17: Mapped[bool] = mapped_column('D17')
    D18: Mapped[bool] = mapped_column('D18')
    D19: Mapped[bool] = mapped_column('D19')
    D20: Mapped[bool] = mapped_column('D20')
    D21: Mapped[bool] = mapped_column('D21')
    D22: Mapped[bool] = mapped_column('D22')
    D23: Mapped[bool] = mapped_column('D23')
    D24: Mapped[bool] = mapped_column('D24')
    D25: Mapped[bool] = mapped_column('D25')
    D26: Mapped[bool] = mapped_column('D26')
    D27: Mapped[bool] = mapped_column('D27')
    D28: Mapped[bool] = mapped_column('D28')
    D29: Mapped[bool] = mapped_column('D29')
    D30: Mapped[bool] = mapped_column('D30')
    D31: Mapped[bool] = mapped_column('D31')
    D32: Mapped[bool] = mapped_column('D32')
    D33: Mapped[bool] = mapped_column('D33')
    D34: Mapped[bool] = mapped_column('D34')
    D35: Mapped[bool] = mapped_column('D35')
    D36: Mapped[bool] = mapped_column('D36')
    D37: Mapped[bool] = mapped_column('D37')
    D38: Mapped[bool] = mapped_column('D38')
    D39: Mapped[bool] = mapped_column('D39')
    D40: Mapped[bool] = mapped_column('D40')
    D41: Mapped[bool] = mapped_column('D41')
    D42: Mapped[bool] = mapped_column('D42')
    D43: Mapped[bool] = mapped_column('D43')
    D44: Mapped[bool] = mapped_column('D44')
    D45: Mapped[bool] = mapped_column('D45')
    D46: Mapped[bool] = mapped_column('D46')
    D47: Mapped[bool] = mapped_column('D47')
    D48: Mapped[bool] = mapped_column('D48')
    D49: Mapped[bool] = mapped_column('D49')
    D50: Mapped[bool] = mapped_column('D50')
    D51: Mapped[bool] = mapped_column('D51')
    D52: Mapped[bool] = mapped_column('D52')
    D53: Mapped[bool] = mapped_column('D53')
    D54: Mapped[bool] = mapped_column('D54')
    D55: Mapped[bool] = mapped_column('D55')
    D56: Mapped[bool] = mapped_column('D56')
    D57: Mapped[bool] = mapped_column('D57')
    D58: Mapped[bool] = mapped_column('D58')
    D59: Mapped[bool] = mapped_column('D59')
    D60: Mapped[bool] = mapped_column('D60')
    D61: Mapped[bool] = mapped_column('D61')
    D62: Mapped[bool] = mapped_column('D62')
    D63: Mapped[bool] = mapped_column('D63')
    D64: Mapped[bool] = mapped_column('D64')
    D65: Mapped[bool] = mapped_column('D65')
    D66: Mapped[bool] = mapped_column('D66')
    D67: Mapped[bool] = mapped_column('D67')
    D68: Mapped[bool] = mapped_column('D68')
    D69: Mapped[bool] = mapped_column('D69')
    D70: Mapped[bool] = mapped_column('D70')
    D71: Mapped[bool] = mapped_column('D71')
    D72: Mapped[bool] = mapped_column('D72')
    D73: Mapped[bool] = mapped_column('D73')
    D74: Mapped[bool] = mapped_column('D74')
    D75: Mapped[bool] = mapped_column('D75')
    D76: Mapped[bool] = mapped_column('D76')
    D77: Mapped[bool] = mapped_column('D77')
    D78: Mapped[bool] = mapped_column('D78')
    D79: Mapped[bool] = mapped_column('D79')
    D80: Mapped[bool] = mapped_column('D80')
    D81: Mapped[bool] = mapped_column('D81')
    D82: Mapped[bool] = mapped_column('D82')
    D83: Mapped[bool] = mapped_column('D83')
    D84: Mapped[bool] = mapped_column('D84')
    D85: Mapped[bool] = mapped_column('D85')
    D86: Mapped[bool] = mapped_column('D86')
    D87: Mapped[bool] = mapped_column('D87')
    D88: Mapped[bool] = mapped_column('D88')
    D89: Mapped[bool] = mapped_column('D89')
    D90: Mapped[bool] = mapped_column('D90')
    D91: Mapped[bool] = mapped_column('D91')
    D92: Mapped[bool] = mapped_column('D92')
    D93: Mapped[bool] = mapped_column('D93')
    D94: Mapped[bool] = mapped_column('D94')
    D95: Mapped[bool] = mapped_column('D95')
    D96: Mapped[bool] = mapped_column('D96')
    D97: Mapped[bool] = mapped_column('D97')
    D98: Mapped[bool] = mapped_column('D98')
    D99: Mapped[bool] = mapped_column('D99')
    D100: Mapped[bool] = mapped_column('D100')
    D101: Mapped[bool] = mapped_column('D101')
    D102: Mapped[bool] = mapped_column('D102')
    D103: Mapped[bool] = mapped_column('D103')
    D104: Mapped[bool] = mapped_column('D104')
    D105: Mapped[bool] = mapped_column('D105')
    D106: Mapped[bool] = mapped_column('D106')
    D107: Mapped[bool] = mapped_column('D107')
    D108: Mapped[bool] = mapped_column('D108')
    D109: Mapped[bool] = mapped_column('D109')
    D110: Mapped[bool] = mapped_column('D110')
    D111: Mapped[bool] = mapped_column('D111')
    D112: Mapped[bool] = mapped_column('D112')
    D113: Mapped[bool] = mapped_column('D113')
    D114: Mapped[bool] = mapped_column('D114')
    D115: Mapped[bool] = mapped_column('D115')
    D116: Mapped[bool] = mapped_column('D116')
    D117: Mapped[bool] = mapped_column('D117')
    D118: Mapped[bool] = mapped_column('D118')
    D119: Mapped[bool] = mapped_column('D119')
    D120: Mapped[bool] = mapped_column('D120')
    D121: Mapped[bool] = mapped_column('D121')
    D122: Mapped[bool] = mapped_column('D122')
    D123: Mapped[bool] = mapped_column('D123')
    D124: Mapped[bool] = mapped_column('D124')
    D125: Mapped[bool] = mapped_column('D125')
    D126: Mapped[bool] = mapped_column('D126')
    D127: Mapped[bool] = mapped_column('D127')
    CkSum: Mapped[int] = mapped_column('CkSum')


class FACIL(Base):
    __tablename__ = 'FACIL'

    ID: Mapped[int] = mapped_column('ID')
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    Facility: Mapped[int] = mapped_column('Facility', primary_key=True)
    Device: Mapped[int] = mapped_column('Device', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    DlFlag: Mapped[int] = mapped_column('DlFlag')
    Notes: Mapped[str] = mapped_column('Notes')
    CkSum: Mapped[int] = mapped_column('CkSum')


class HOL(Base):
    __tablename__ = 'HOL'

    ID: Mapped[int] = mapped_column('ID')
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    HolDate: Mapped[DateTime] = mapped_column('HolDate', primary_key=True)
    Type: Mapped[int] = mapped_column('Type')
    Name: Mapped[str] = mapped_column('Name')
    DlFlag: Mapped[int] = mapped_column('DlFlag')
    Notes: Mapped[str] = mapped_column('Notes')
    CkSum: Mapped[int] = mapped_column('CkSum')
    ReOccurring: Mapped[bool] = mapped_column('ReOccurring')


class KeyName(Base):
    __tablename__ = 'KeyName'

    ID: Mapped[int] = mapped_column('ID')
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    Name: Mapped[str] = mapped_column('Name', primary_key=True)
    Door: Mapped[str] = mapped_column('Door')
    KeyType: Mapped[str] = mapped_column('KeyType')
    Pinning: Mapped[str] = mapped_column('Pinning')
    Notes: Mapped[str] = mapped_column('Notes')


class LocCards(Base):
    __tablename__ = 'LocCards'

    ID: Mapped[int] = mapped_column('ID')
    CardID: Mapped[int] = mapped_column('CardID', ForeignKey('CARDS.ID'), primary_key=True)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    Acl: Mapped[int] = mapped_column('Acl')
    Oll: Mapped[int] = mapped_column('Oll')
    LastDate: Mapped[DateTime] = mapped_column('LastDate')
    LastDev: Mapped[int] = mapped_column('LastDev')
    InOut1: Mapped[str] = mapped_column('InOut1')
    InOut2: Mapped[str] = mapped_column('InOut2')
    InOut3: Mapped[str] = mapped_column('InOut3')
    InOut4: Mapped[str] = mapped_column('InOut4')
    DlFlag: Mapped[int] = mapped_column('DlFlag')
    CkSum: Mapped[int] = mapped_column('CkSum')
    Acl1: Mapped[int] = mapped_column('Acl1')
    Acl2: Mapped[int] = mapped_column('Acl2')
    Acl3: Mapped[int] = mapped_column('Acl3')
    Acl4: Mapped[int] = mapped_column('Acl4')


class LocMem(Base):
    __tablename__ = 'LocMem'

    ID: Mapped[int] = mapped_column('ID')
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    TableNum: Mapped[int] = mapped_column('TableNum', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    NumRecs: Mapped[int] = mapped_column('NumRecs')
    MaxRecs: Mapped[int] = mapped_column('MaxRecs')
    BytesEach: Mapped[int] = mapped_column('BytesEach')
    TotalBytes: Mapped[int] = mapped_column('TotalBytes')


class MSG(Base):
    __tablename__ = 'MSG'

    ID: Mapped[int] = mapped_column('ID')
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), primary_key=True)
    Name: Mapped[str] = mapped_column('Name', primary_key=True)
    Msg: Mapped[str] = mapped_column('Msg')


class MapName(Base):
    __tablename__ = 'MapName'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'))
    Name: Mapped[str] = mapped_column('Name')
    FileName: Mapped[str] = mapped_column('FileName')
    Icon: Mapped[int] = mapped_column('Icon')
    DispOrder: Mapped[int] = mapped_column('DispOrder')
    Notes: Mapped[str] = mapped_column('Notes')
    Height: Mapped[int] = mapped_column('Height')
    Width: Mapped[int] = mapped_column('Width')


class MapPoint(Base):
    __tablename__ = 'MapPoint'

    ID: Mapped[int] = mapped_column('ID')
    MapID: Mapped[int] = mapped_column('MapID', ForeignKey('MapName.ID'))
    PointID: Mapped[int] = mapped_column('PointID')
    PointType: Mapped[int] = mapped_column('PointType')
    XPos: Mapped[int] = mapped_column('XPos')
    YPos: Mapped[int] = mapped_column('YPos')


class NAMES(Base):
    __tablename__ = 'NAMES'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp')
    LName: Mapped[str] = mapped_column('LName')
    FName: Mapped[str] = mapped_column('FName')
    Company: Mapped[int] = mapped_column('Company')
    Visitor: Mapped[bool] = mapped_column('Visitor')
    Trace: Mapped[bool] = mapped_column('Trace')
    PrintIt: Mapped[bool] = mapped_column('PrintIt')
    Notes: Mapped[str] = mapped_column('Notes')


class EmailGrp(Base):
    __tablename__ = 'EmailGrp'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    EmailGrpNameID: Mapped[int] = mapped_column('EmailGrpNameID', ForeignKey('EmailGrpName.ID'))
    NameID: Mapped[int] = mapped_column('NameID', ForeignKey('NAMES.ID'))
    TZ: Mapped[int] = mapped_column('TZ')


class Images(Base):
    __tablename__ = 'Images'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    NameID: Mapped[int] = mapped_column('NameID', ForeignKey('NAMES.ID'))
    ImgType: Mapped[int] = mapped_column('ImgType')
    FileName: Mapped[str] = mapped_column('FileName')


class Keys(Base):
    __tablename__ = 'Keys'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    KeyID: Mapped[int] = mapped_column('KeyID', ForeignKey('KeyName.ID'))
    NameID: Mapped[int] = mapped_column('NameID', ForeignKey('NAMES.ID'))
    Returned: Mapped[bool] = mapped_column('Returned')
    Issued: Mapped[DateTime] = mapped_column('Issued')
    IssueNum: Mapped[int] = mapped_column('IssueNum')


class OGRP(Base):
    __tablename__ = 'OGRP'

    ID: Mapped[int] = mapped_column('ID')
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    Ogrp: Mapped[int] = mapped_column('Ogrp', primary_key=True)
    IO: Mapped[int] = mapped_column('IO', primary_key=True)
    IOType: Mapped[int] = mapped_column('IOType', primary_key=True)
    RespType: Mapped[int] = mapped_column('RespType')
    SetTime: Mapped[int] = mapped_column('SetTime')
    TimeType: Mapped[str] = mapped_column('TimeType')
    TZ: Mapped[int] = mapped_column('TZ')
    DlFlag: Mapped[int] = mapped_column('DlFlag')
    CkSum: Mapped[int] = mapped_column('CkSum')


class OLL(Base):
    __tablename__ = 'OLL'

    ID: Mapped[int] = mapped_column('ID')
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    Oll: Mapped[int] = mapped_column('Oll', primary_key=True)
    Device: Mapped[int] = mapped_column('Device', primary_key=True)
    Ogrp: Mapped[int] = mapped_column('Ogrp', primary_key=True)
    DlFlag: Mapped[int] = mapped_column('DlFlag')
    CkSum: Mapped[int] = mapped_column('CkSum')


class OgrpName(Base):
    __tablename__ = 'OgrpName'

    ID: Mapped[int] = mapped_column('ID')
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    Ogrp: Mapped[int] = mapped_column('Ogrp', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    Notes: Mapped[str] = mapped_column('Notes')


class OllName(Base):
    __tablename__ = 'OllName'

    ID: Mapped[int] = mapped_column('ID')
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    Oll: Mapped[int] = mapped_column('Oll', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    Notes: Mapped[str] = mapped_column('Notes')
    Visitor: Mapped[bool] = mapped_column('Visitor')


class OprCom(Base):
    __tablename__ = 'OprCom'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    Comment: Mapped[str] = mapped_column('Comment')
    DispOrder: Mapped[int] = mapped_column('DispOrder')


class OvrGrpName(Base):
    __tablename__ = 'OvrGrpName'

    ID: Mapped[int] = mapped_column('ID')
    LocGrp: Mapped[int] = mapped_column('LocGrp', primary_key=True)
    Name: Mapped[str] = mapped_column('Name', primary_key=True)
    GrpType: Mapped[int] = mapped_column('GrpType')
    Icon1: Mapped[int] = mapped_column('Icon1')
    Icon2: Mapped[int] = mapped_column('Icon2')
    Notes: Mapped[str] = mapped_column('Notes')
    DispOrder: Mapped[int] = mapped_column('DispOrder')


class OvrGrp(Base):
    __tablename__ = 'OvrGrp'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    OvrGrpID: Mapped[int] = mapped_column('OvrGrpID', ForeignKey('OvrGrpName.ID'))
    PointID: Mapped[int] = mapped_column('PointID')


class OvrSchedule(Base):
    __tablename__ = 'OvrSchedule'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    PointID: Mapped[int] = mapped_column('PointID')
    PointType: Mapped[int] = mapped_column('PointType')
    StartCmd: Mapped[int] = mapped_column('StartCmd')
    StartDate: Mapped[DateTime] = mapped_column('StartDate')
    StopCmd: Mapped[int] = mapped_column('StopCmd')
    StopDate: Mapped[DateTime] = mapped_column('StopDate')
    Opr: Mapped[str] = mapped_column('Opr')
    OprID: Mapped[int] = mapped_column('OprID')
    Status: Mapped[int] = mapped_column('Status')


class OvrSchedule2(Base):
    __tablename__ = 'OvrSchedule2'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    PointID: Mapped[int] = mapped_column('PointID')
    PointType: Mapped[int] = mapped_column('PointType')
    StartCmd: Mapped[int] = mapped_column('StartCmd')
    StartDate: Mapped[DateTime] = mapped_column('StartDate')
    StopCmd: Mapped[int] = mapped_column('StopCmd')
    StopDate: Mapped[DateTime] = mapped_column('StopDate')
    Opr: Mapped[str] = mapped_column('Opr')
    OprID: Mapped[int] = mapped_column('OprID')
    Status: Mapped[int] = mapped_column('Status')


class PHONE(Base):
    __tablename__ = 'PHONE'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    NameID: Mapped[int] = mapped_column('NameID', ForeignKey('NAMES.ID'))
    Name: Mapped[str] = mapped_column('Name')
    Phone: Mapped[str] = mapped_column('Phone')
    Notes: Mapped[str] = mapped_column('Notes')


class SkillName(Base):
    __tablename__ = 'SkillName'

    ID: Mapped[int] = mapped_column('ID')
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), primary_key=True)
    Name: Mapped[str] = mapped_column('Name', primary_key=True)


class Skills(Base):
    __tablename__ = 'Skills'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    SkillID: Mapped[int] = mapped_column('SkillID', ForeignKey('SkillName.ID'))
    NameID: Mapped[int] = mapped_column('NameID', ForeignKey('NAMES.ID'))


class TZ(Base):
    __tablename__ = 'TZ'

    ID: Mapped[int] = mapped_column('ID')
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    TZ: Mapped[int] = mapped_column('TZ', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    LinkStatus: Mapped[int] = mapped_column('LinkStatus')
    SunStart: Mapped[int] = mapped_column('SunStart')
    SunStop: Mapped[int] = mapped_column('SunStop')
    MonStart: Mapped[int] = mapped_column('MonStart')
    MonStop: Mapped[int] = mapped_column('MonStop')
    TueStart: Mapped[int] = mapped_column('TueStart')
    TueStop: Mapped[int] = mapped_column('TueStop')
    WedStart: Mapped[int] = mapped_column('WedStart')
    WedStop: Mapped[int] = mapped_column('WedStop')
    ThuStart: Mapped[int] = mapped_column('ThuStart')
    ThuStop: Mapped[int] = mapped_column('ThuStop')
    FriStart: Mapped[int] = mapped_column('FriStart')
    FriStop: Mapped[int] = mapped_column('FriStop')
    SatStart: Mapped[int] = mapped_column('SatStart')
    SatStop: Mapped[int] = mapped_column('SatStop')
    Hol1Start: Mapped[int] = mapped_column('Hol1Start')
    Hol1Stop: Mapped[int] = mapped_column('Hol1Stop')
    Hol2Start: Mapped[int] = mapped_column('Hol2Start')
    Hol2Stop: Mapped[int] = mapped_column('Hol2Stop')
    Hol3Start: Mapped[int] = mapped_column('Hol3Start')
    Hol3Stop: Mapped[int] = mapped_column('Hol3Stop')
    DlFlag: Mapped[int] = mapped_column('DlFlag')
    Notes: Mapped[str] = mapped_column('Notes')
    CkSum: Mapped[int] = mapped_column('CkSum')


class UdfName(Base):
    __tablename__ = 'UdfName'

    ID: Mapped[int] = mapped_column('ID')
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), primary_key=True)
    UdfNum: Mapped[int] = mapped_column('UdfNum', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    Required: Mapped[bool] = mapped_column('Required')
    Uniq: Mapped[bool] = mapped_column('Uniq')
    Mask: Mapped[str] = mapped_column('Mask')
    StopDate: Mapped[bool] = mapped_column('StopDate')
    VisitorID: Mapped[bool] = mapped_column('VisitorID')
    CardNum: Mapped[bool] = mapped_column('CardNum')
    Hidden: Mapped[bool] = mapped_column('Hidden')
    Combo: Mapped[bool] = mapped_column('Combo')
    ComboOnly: Mapped[bool] = mapped_column('ComboOnly')
    Email: Mapped[bool] = mapped_column('Email')


class UDF(Base):
    __tablename__ = 'UDF'

    ID: Mapped[int] = mapped_column('ID')
    LocGrp: Mapped[int] = mapped_column('LocGrp')
    NameID: Mapped[int] = mapped_column('NameID', ForeignKey('NAMES.ID'), primary_key=True)
    UdfNum: Mapped[int] = mapped_column('UdfNum', primary_key=True)
    UdfText: Mapped[str] = mapped_column('UdfText')


class UdfSel(Base):
    __tablename__ = 'UdfSel'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp')
    UdfNum: Mapped[int] = mapped_column('UdfNum')
    ListOrder: Mapped[int] = mapped_column('ListOrder')
    SelText: Mapped[str] = mapped_column('SelText')


class Wav(Base):
    __tablename__ = 'Wav'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    FileName: Mapped[str] = mapped_column('FileName')


class WorkStations(Base):
    __tablename__ = 'WorkStations'

    ID: Mapped[int] = mapped_column('ID', primary_key=True)
    WorkSta: Mapped[int] = mapped_column('WorkSta')
    Name: Mapped[str] = mapped_column('Name')
    LastUsed: Mapped[DateTime] = mapped_column('LastUsed')
