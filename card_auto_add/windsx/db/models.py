from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class AcsDataBase(DeclarativeBase):
    pass


class ACL(AcsDataBase):
    __tablename__ = 'ACL'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True, default=1)
    Acl: Mapped[int] = mapped_column('Acl', primary_key=True, default=1)
    Tz: Mapped[int] = mapped_column('Tz', primary_key=True, default=1)
    DGrp: Mapped[int] = mapped_column('DGrp', primary_key=True, default=1)
    DlFlag: Mapped[int] = mapped_column('DlFlag', nullable=True, default=0)
    CkSum: Mapped[int] = mapped_column('CkSum', nullable=True, default=0)


class CameraName(AcsDataBase):
    __tablename__ = 'CameraName'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    Loc: Mapped[int] = mapped_column('Loc', primary_key=True, default=0)
    Name: Mapped[str] = mapped_column('Name', primary_key=True)
    Icon1: Mapped[int] = mapped_column('Icon1', nullable=True, default=1)
    ListOrder: Mapped[int] = mapped_column('ListOrder', nullable=True, default=0)
    Notes: Mapped[str] = mapped_column('Notes', default='')
    IOID: Mapped[int] = mapped_column('IOID', default=0)
    CamType: Mapped[int] = mapped_column('CamType', default=0)
    SvrName: Mapped[str] = mapped_column('SvrName', default='')
    CamSel: Mapped[str] = mapped_column('CamSel', default='')
    PTZ: Mapped[bool] = mapped_column('PTZ', nullable=True, default=False)
    Hist: Mapped[int] = mapped_column('Hist', nullable=True, default=0)
    PreSet: Mapped[int] = mapped_column('PreSet', nullable=True, default=0)
    DvrUser: Mapped[str] = mapped_column('DvrUser', default='')
    DvrPw: Mapped[str] = mapped_column('DvrPw', default='')


class CommSvr(AcsDataBase):
    __tablename__ = 'CommSvr'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    Name: Mapped[str] = mapped_column('Name')
    WorkSta: Mapped[int] = mapped_column('WorkSta', primary_key=True, default=0)
    IPAddress: Mapped[str] = mapped_column('IPAddress')
    IPName: Mapped[str] = mapped_column('IPName', default='_')
    Throttle: Mapped[int] = mapped_column('Throttle', nullable=True, default=1000)
    SaveDBEdits: Mapped[bool] = mapped_column('SaveDBEdits', nullable=True, default=False)
    BuCsAddress: Mapped[str] = mapped_column('BuCsAddress', nullable=True, default='0')
    EKey: Mapped[str] = mapped_column('EKey', default='')


class DataBaseInfo(AcsDataBase):
    __tablename__ = 'DataBaseInfo'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    DataBaseVersion: Mapped[int] = mapped_column('DataBaseVersion', nullable=True, default=0)
    LastBackUp: Mapped[datetime] = mapped_column('LastBackUp', nullable=True,
                                                 default=datetime(year=1800, month=12, day=31, hour=0, minute=0,
                                                                  second=0))
    Opr: Mapped[int] = mapped_column('Opr', nullable=True, default=0)
    InstallDate: Mapped[datetime] = mapped_column('InstallDate', nullable=True,
                                                  default=datetime(year=1899, month=12, day=31, hour=0, minute=0,
                                                                   second=0))
    Register: Mapped[bool] = mapped_column('Register', nullable=True)
    SmContract: Mapped[bool] = mapped_column('SmContract', nullable=True)
    ContractDate: Mapped[datetime] = mapped_column('ContractDate', nullable=True,
                                                   default=datetime(year=1899, month=12, day=31, hour=0, minute=0,
                                                                    second=0))
    ServiceCode: Mapped[str] = mapped_column('ServiceCode', default='No Contract')
    Opc: Mapped[str] = mapped_column('Opc', nullable=True, default='0')


class EmailGrpName(AcsDataBase):
    __tablename__ = 'EmailGrpName'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp')
    Name: Mapped[str] = mapped_column('Name')
    Notes: Mapped[str] = mapped_column('Notes', default='')


class IO(AcsDataBase):
    __tablename__ = 'IO'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True, default=0)
    Device: Mapped[int] = mapped_column('Device', primary_key=True)
    IO: Mapped[int] = mapped_column('IO', primary_key=True)
    Type: Mapped[str] = mapped_column('Type', primary_key=True, default='I')
    Name: Mapped[str] = mapped_column('Name')
    T1: Mapped[int] = mapped_column('T1', nullable=True, default=0)
    T2: Mapped[int] = mapped_column('T2', nullable=True, default=0)
    T3: Mapped[int] = mapped_column('T3', nullable=True, default=0)
    T4: Mapped[int] = mapped_column('T4', nullable=True, default=0)
    AbortDelay: Mapped[int] = mapped_column('AbortDelay', nullable=True, default=0)
    Ogrp: Mapped[int] = mapped_column('Ogrp', nullable=True, default=0)
    LinkStatus: Mapped[str] = mapped_column('LinkStatus', default='S')
    ActionMsg: Mapped[int] = mapped_column('ActionMsg', nullable=True, default=0)
    ReportChg: Mapped[bool] = mapped_column('ReportChg', nullable=True, default=False)
    AlarmPri: Mapped[int] = mapped_column('AlarmPri', nullable=True, default=0)
    CircuitType: Mapped[int] = mapped_column('CircuitType', nullable=True, default=0)
    StatusPort: Mapped[int] = mapped_column('StatusPort', nullable=True, default=0)
    NormMsg: Mapped[int] = mapped_column('NormMsg', nullable=True, default=0)
    AbnormMsg: Mapped[int] = mapped_column('AbnormMsg', nullable=True, default=0)
    AlarmPort: Mapped[int] = mapped_column('AlarmPort', nullable=True, default=0)
    AlarmMsg: Mapped[int] = mapped_column('AlarmMsg', nullable=True, default=0)
    RestorMsg: Mapped[int] = mapped_column('RestorMsg', nullable=True, default=0)
    ReportFlag: Mapped[bool] = mapped_column('ReportFlag', nullable=True, default=False)
    FailSecure: Mapped[bool] = mapped_column('FailSecure', nullable=True, default=False)
    OpenName: Mapped[str] = mapped_column('OpenName', default='OPEN')
    SecuName: Mapped[str] = mapped_column('SecuName', default='SECURE')
    LinkState: Mapped[str] = mapped_column('LinkState', default='O')
    WireTag: Mapped[str] = mapped_column('WireTag', default='')
    Icon1: Mapped[int] = mapped_column('Icon1', nullable=True, default=1)
    Icon2: Mapped[int] = mapped_column('Icon2', nullable=True, default=2)
    AlarmWav: Mapped[int] = mapped_column('AlarmWav', nullable=True, default=0)
    DlFlag: Mapped[int] = mapped_column('DlFlag', nullable=True, default=0)
    Notes: Mapped[str] = mapped_column('Notes', default='')
    AlarmMap: Mapped[bool] = mapped_column('AlarmMap', nullable=True)
    AlarmResolve: Mapped[bool] = mapped_column('AlarmResolve', nullable=True, default=False)
    AlarmEcho: Mapped[bool] = mapped_column('AlarmEcho', nullable=True, default=False)
    ListOrder: Mapped[int] = mapped_column('ListOrder', nullable=True, default=0)
    ReqComment: Mapped[bool] = mapped_column('ReqComment', nullable=True, default=False)
    CameraID: Mapped[int] = mapped_column('CameraID', nullable=True, default=0)
    AlarmCam: Mapped[bool] = mapped_column('AlarmCam', nullable=True, default=False)
    ElevDev: Mapped[int] = mapped_column('ElevDev', default=-1)
    AlarmEmail: Mapped[int] = mapped_column('AlarmEmail', nullable=True, default=0)


class Icons(AcsDataBase):
    __tablename__ = 'Icons'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    FileName: Mapped[str] = mapped_column('FileName')


class ImageSrcName(AcsDataBase):
    __tablename__ = 'ImageSrcName'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    Name: Mapped[str] = mapped_column('Name')
    FileExt: Mapped[str] = mapped_column('FileExt', default='JPG')
    QFactor: Mapped[int] = mapped_column('QFactor', default=20)
    SrcType: Mapped[int] = mapped_column('SrcType', nullable=True, default=0)
    CommPort: Mapped[int] = mapped_column('CommPort', nullable=True, default=0)
    Notes: Mapped[str] = mapped_column('Notes', default='')


class ImageSrc(AcsDataBase):
    __tablename__ = 'ImageSrc'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    SourceID: Mapped[int] = mapped_column('SourceID', ForeignKey('ImageSrcName.ID'), nullable=True, default=0)
    WorkSta: Mapped[int] = mapped_column('WorkSta', nullable=True, default=0)
    ExecOrder: Mapped[int] = mapped_column('ExecOrder', default=0)
    CmdType: Mapped[str] = mapped_column('CmdType')
    CmdString: Mapped[str] = mapped_column('CmdString', nullable=True)


class LocGrp(AcsDataBase):
    __tablename__ = 'LocGrp'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', primary_key=True, default=0)
    Name: Mapped[str] = mapped_column('Name', default='')
    NDigits: Mapped[int] = mapped_column('NDigits', default=4)
    DupPin: Mapped[bool] = mapped_column('DupPin', nullable=True, default=False)
    HexCodes: Mapped[bool] = mapped_column('HexCodes', nullable=True, default=False)
    AsciiCodes: Mapped[bool] = mapped_column('AsciiCodes', nullable=True, default=False)
    WsPrintingNames: Mapped[str] = mapped_column('WsPrintingNames', nullable=True, default='None')
    TimePrintStarted: Mapped[datetime] = mapped_column('TimePrintStarted', nullable=True)


class AclGrpName(AcsDataBase):
    __tablename__ = 'AclGrpName'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), default=1)
    Name: Mapped[str] = mapped_column('Name')
    Notes: Mapped[str] = mapped_column('Notes', default='')
    Visitor: Mapped[bool] = mapped_column('Visitor', nullable=True)
    IsMaster: Mapped[bool] = mapped_column('IsMaster', nullable=True, default=False)


class AclGrpCombo(AcsDataBase):
    __tablename__ = 'AclGrpCombo'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    AclGrpNameID: Mapped[int] = mapped_column('AclGrpNameID', ForeignKey('AclGrpName.ID'), default=0)
    ComboID: Mapped[int] = mapped_column('ComboID', default=0)
    LocGrp: Mapped[int] = mapped_column('LocGrp', nullable=True, default=0)


class BdgName(AcsDataBase):
    __tablename__ = 'BdgName'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), default=1)
    Name: Mapped[str] = mapped_column('Name')
    XSize: Mapped[int] = mapped_column('XSize', default=2894)
    YSize: Mapped[int] = mapped_column('YSize', default=4594)
    XOffSet: Mapped[int] = mapped_column('XOffSet', default=0)
    YOffSet: Mapped[int] = mapped_column('YOffSet', default=0)
    MagStripe1: Mapped[str] = mapped_column('MagStripe1')
    MagStripe2: Mapped[str] = mapped_column('MagStripe2')
    MagStripe3: Mapped[str] = mapped_column('MagStripe3')
    BdgType: Mapped[int] = mapped_column('BdgType', default=0)
    FilterIndex: Mapped[int] = mapped_column('FilterIndex', default=1)
    Notes: Mapped[str] = mapped_column('Notes', default='')


class Badge(AcsDataBase):
    __tablename__ = 'Badge'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    BadgeID: Mapped[int] = mapped_column('BadgeID', ForeignKey('BdgName.ID'))
    ZOrder: Mapped[int] = mapped_column('ZOrder', default=0)
    FieldType: Mapped[str] = mapped_column('FieldType')
    Name: Mapped[str] = mapped_column('Name')
    XPos: Mapped[int] = mapped_column('XPos', default=0)
    YPos: Mapped[int] = mapped_column('YPos', default=0)
    XSize: Mapped[int] = mapped_column('XSize', default=1)
    YSize: Mapped[int] = mapped_column('YSize', default=1)
    Center: Mapped[bool] = mapped_column('Center', nullable=True, default=False)
    Shrink2Fit: Mapped[bool] = mapped_column('Shrink2Fit', nullable=True, default=False)
    BarCode: Mapped[bool] = mapped_column('BarCode', nullable=True, default=False)
    BcFormat: Mapped[str] = mapped_column('BcFormat', default='25123ccccccc')
    Aspect: Mapped[bool] = mapped_column('Aspect', nullable=True)
    ChromaKey: Mapped[bool] = mapped_column('ChromaKey', nullable=True)
    MagSTrack: Mapped[int] = mapped_column('MagSTrack', nullable=True, default=0)
    MaxChars: Mapped[int] = mapped_column('MaxChars', nullable=True, default=0)
    Rotation: Mapped[int] = mapped_column('Rotation', nullable=True, default=0)
    RGB: Mapped[int] = mapped_column('RGB', default=0)
    FName: Mapped[str] = mapped_column('FName')
    FSize: Mapped[int] = mapped_column('FSize', default=8)
    FBold: Mapped[bool] = mapped_column('FBold', nullable=True, default=False)
    FItalic: Mapped[bool] = mapped_column('FItalic', nullable=True, default=False)
    FUnderLine: Mapped[bool] = mapped_column('FUnderLine', nullable=True, default=False)
    TexRecXPos: Mapped[int] = mapped_column('TexRecXPos', default=0)
    TexRecYPos: Mapped[int] = mapped_column('TexRecYPos', default=0)
    TexRecXSize: Mapped[int] = mapped_column('TexRecXSize', default=0)
    TexRecYSize: Mapped[int] = mapped_column('TexRecYSize', default=0)
    Ghost: Mapped[int] = mapped_column('Ghost', nullable=True, default=0)


class CARDS(AcsDataBase):
    __tablename__ = 'CARDS'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    NameID: Mapped[int] = mapped_column('NameID')
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), primary_key=True)
    Code: Mapped[float] = mapped_column('Code', primary_key=True, default=1.0)
    Pin: Mapped[int] = mapped_column('Pin', nullable=True, default=0)
    StartDate: Mapped[datetime] = mapped_column('StartDate',
                                                default=datetime(year=1000, month=1, day=1, hour=0, minute=0, second=0))
    StopDate: Mapped[datetime] = mapped_column('StopDate',
                                               default=datetime(year=9999, month=12, day=31, hour=0, minute=0,
                                                                second=0))
    Status: Mapped[bool] = mapped_column('Status', nullable=True)
    CardNum: Mapped[str] = mapped_column('CardNum', nullable=True)
    GTour: Mapped[bool] = mapped_column('GTour', nullable=True)
    NumUses: Mapped[int] = mapped_column('NumUses', default=9999)
    Notes: Mapped[str] = mapped_column('Notes', default='')
    DlFlag: Mapped[int] = mapped_column('DlFlag', nullable=True, default=0)
    AclGrpComboID: Mapped[int] = mapped_column('AclGrpComboID', nullable=True, default=0)
    APB: Mapped[bool] = mapped_column('APB', nullable=True, default=False)
    TempAclGrpComboID: Mapped[int] = mapped_column('TempAclGrpComboID', nullable=True, default=0)
    AclStartDate: Mapped[datetime] = mapped_column('AclStartDate',
                                                   default=datetime(year=9999, month=12, day=31, hour=0, minute=0,
                                                                    second=0))
    AclStopDate: Mapped[datetime] = mapped_column('AclStopDate',
                                                  default=datetime(year=9999, month=12, day=31, hour=0, minute=0,
                                                                   second=0))
    TempAcl: Mapped[bool] = mapped_column('TempAcl', nullable=True, default=False)


class COMPANY(AcsDataBase):
    __tablename__ = 'COMPANY'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), primary_key=True)
    Company: Mapped[int] = mapped_column('Company', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    Phone: Mapped[str] = mapped_column('Phone', default='')
    Fax: Mapped[str] = mapped_column('Fax', default='')
    Contact: Mapped[str] = mapped_column('Contact', default='')
    Suite: Mapped[str] = mapped_column('Suite', default='')
    Badge: Mapped[int] = mapped_column('Badge', nullable=True, default=0)
    Notes: Mapped[str] = mapped_column('Notes', default='')
    NoUseDays: Mapped[int] = mapped_column('NoUseDays', nullable=True, default=0)


class GtsName(AcsDataBase):
    __tablename__ = 'GtsName'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), primary_key=True)
    GtsNum: Mapped[int] = mapped_column('GtsNum', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    Random: Mapped[bool] = mapped_column('Random', nullable=True)
    Notes: Mapped[str] = mapped_column('Notes', default='')
    StartTime: Mapped[datetime] = mapped_column('StartTime', nullable=True)
    CurrentStation: Mapped[int] = mapped_column('CurrentStation', nullable=True, default=0)
    LastStationTime: Mapped[datetime] = mapped_column('LastStationTime', nullable=True)
    IsPaused: Mapped[bool] = mapped_column('IsPaused', nullable=True, default=False)


class GTS(AcsDataBase):
    __tablename__ = 'GTS'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', primary_key=True, default=0)
    GtsNum: Mapped[int] = mapped_column('GtsNum', primary_key=True)
    StaNum: Mapped[int] = mapped_column('StaNum', primary_key=True)
    PointID: Mapped[int] = mapped_column('PointID')
    PointType: Mapped[str] = mapped_column('PointType')
    Event: Mapped[int] = mapped_column('Event')
    MinTime: Mapped[int] = mapped_column('MinTime')
    MaxTime: Mapped[int] = mapped_column('MaxTime')
    ActionMsg: Mapped[int] = mapped_column('ActionMsg', nullable=True, default=0)


class HistRptName(AcsDataBase):
    __tablename__ = 'HistRptName'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), primary_key=True, default=0)
    Name: Mapped[str] = mapped_column('Name', primary_key=True)
    StartDateOffSet: Mapped[int] = mapped_column('StartDateOffSet', nullable=True, default=0)
    StopDateOffSet: Mapped[int] = mapped_column('StopDateOffSet', nullable=True, default=0)
    StartTime: Mapped[int] = mapped_column('StartTime', nullable=True, default=0)
    StopTime: Mapped[int] = mapped_column('StopTime', nullable=True, default=0)
    DailyStartStop: Mapped[bool] = mapped_column('DailyStartStop', nullable=True, default=False)
    AllEvn: Mapped[bool] = mapped_column('AllEvn', nullable=True, default=True)
    AllDev: Mapped[bool] = mapped_column('AllDev', nullable=True, default=True)
    AllNames: Mapped[bool] = mapped_column('AllNames', nullable=True, default=True)
    TNA: Mapped[bool] = mapped_column('TNA', nullable=True, default=False)
    SortByTime: Mapped[bool] = mapped_column('SortByTime', nullable=True)
    Uses: Mapped[bool] = mapped_column('Uses', nullable=True)
    NameSort: Mapped[bool] = mapped_column('NameSort', nullable=True)
    Summary: Mapped[bool] = mapped_column('Summary', nullable=True)
    Notes: Mapped[str] = mapped_column('Notes', default='')
    DispCodes: Mapped[bool] = mapped_column('DispCodes', nullable=True)
    Elevator: Mapped[bool] = mapped_column('Elevator', nullable=True, default=False)


class HistRptDetail(AcsDataBase):
    __tablename__ = 'HistRptDetail'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    RptID: Mapped[int] = mapped_column('RptID', ForeignKey('HistRptName.ID'), nullable=True, default=0)
    Detail: Mapped[str] = mapped_column('Detail', nullable=True)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), default=0)
    Device: Mapped[int] = mapped_column('Device', default=0)
    IO: Mapped[int] = mapped_column('IO', default=0)


class ImageType(AcsDataBase):
    __tablename__ = 'ImageType'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), primary_key=True, default=1)
    Num: Mapped[int] = mapped_column('Num', primary_key=True, default=0)
    Name: Mapped[str] = mapped_column('Name')
    Source: Mapped[int] = mapped_column('Source', default=0)
    DefaultImage: Mapped[bool] = mapped_column('DefaultImage', nullable=True)
    GrayScale: Mapped[bool] = mapped_column('GrayScale', nullable=True)
    CapOrder: Mapped[int] = mapped_column('CapOrder', default=1)
    Notes: Mapped[str] = mapped_column('Notes', default='')


class LOC(AcsDataBase):
    __tablename__ = 'LOC'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    Loc: Mapped[int] = mapped_column('Loc', primary_key=True, default=1)
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), default=1)
    Name: Mapped[str] = mapped_column('Name')
    Address: Mapped[str] = mapped_column('Address', default='')
    City: Mapped[str] = mapped_column('City', default='')
    State: Mapped[str] = mapped_column('State', default='')
    Zip: Mapped[str] = mapped_column('Zip', default='')
    Status: Mapped[bool] = mapped_column('Status', nullable=True, default=True)
    PlFlag: Mapped[bool] = mapped_column('PlFlag', nullable=True, default=False)
    FullDlFlag: Mapped[bool] = mapped_column('FullDlFlag', nullable=True, default=False)
    LoFlag: Mapped[bool] = mapped_column('LoFlag', nullable=True, default=False)
    PlTime: Mapped[datetime] = mapped_column('PlTime', nullable=True)
    DelayPl: Mapped[int] = mapped_column('DelayPl', nullable=True, default=0)
    AfterHoursPl: Mapped[bool] = mapped_column('AfterHoursPl', nullable=True)
    LocPw: Mapped[str] = mapped_column('LocPw', default='')
    ConnType: Mapped[str] = mapped_column('ConnType', default='I')
    Phone: Mapped[str] = mapped_column('Phone', default='')
    PcPhone: Mapped[str] = mapped_column('PcPhone', default='')
    CheckTime: Mapped[int] = mapped_column('CheckTime', nullable=True, default=120)
    LogRepEn: Mapped[bool] = mapped_column('LogRepEn', nullable=True, default=True)
    DevRepEn: Mapped[bool] = mapped_column('DevRepEn', nullable=True, default=True)
    MastIsDev: Mapped[bool] = mapped_column('MastIsDev', nullable=True, default=True)
    LinkEn: Mapped[bool] = mapped_column('LinkEn', nullable=True, default=False)
    OllEn: Mapped[bool] = mapped_column('OllEn', nullable=True, default=False)
    AntiPassEn: Mapped[bool] = mapped_column('AntiPassEn', nullable=True, default=False)
    CrWithKp: Mapped[bool] = mapped_column('CrWithKp', nullable=True, default=False)
    DeniedsAl: Mapped[int] = mapped_column('DeniedsAl', nullable=True, default=3)
    WeigNoise: Mapped[bool] = mapped_column('WeigNoise', nullable=True, default=False)
    DBadCard: Mapped[bool] = mapped_column('DBadCard', nullable=True, default=False)
    AlResAk: Mapped[bool] = mapped_column('AlResAk', nullable=True, default=False)
    AutoForgive: Mapped[bool] = mapped_column('AutoForgive', nullable=True)
    MissFail: Mapped[int] = mapped_column('MissFail', nullable=True, default=3)
    HoursDiff: Mapped[int] = mapped_column('HoursDiff', nullable=True, default=0)
    ActionMsg: Mapped[int] = mapped_column('ActionMsg', nullable=True, default=0)
    LastComm: Mapped[datetime] = mapped_column('LastComm', nullable=True,
                                               default=datetime(year=1899, month=1, day=2, hour=0, minute=0, second=0))
    CommErr: Mapped[int] = mapped_column('CommErr', nullable=True, default=0)
    NodeCs: Mapped[int] = mapped_column('NodeCs', default=0)
    OGrpCs: Mapped[int] = mapped_column('OGrpCs', default=0)
    HolCs: Mapped[int] = mapped_column('HolCs', default=0)
    FacilCs: Mapped[int] = mapped_column('FacilCs', default=0)
    OllCs: Mapped[int] = mapped_column('OllCs', default=0)
    TzCs: Mapped[int] = mapped_column('TzCs', default=0)
    AclCs: Mapped[int] = mapped_column('AclCs', default=0)
    DGrpCs: Mapped[int] = mapped_column('DGrpCs', default=0)
    CodeCs: Mapped[int] = mapped_column('CodeCs', default=0)
    DlFlag: Mapped[int] = mapped_column('DlFlag', nullable=True, default=0)
    RAM: Mapped[int] = mapped_column('RAM', nullable=True, default=0)
    FwVersion: Mapped[int] = mapped_column('FwVersion', nullable=True, default=0)
    FwDate: Mapped[datetime] = mapped_column('FwDate', nullable=True)
    CpuType: Mapped[int] = mapped_column('CpuType', nullable=True, default=0)
    IoType: Mapped[int] = mapped_column('IoType', nullable=True, default=0)
    Notes: Mapped[str] = mapped_column('Notes', default='')
    EchoLoc: Mapped[int] = mapped_column('EchoLoc', nullable=True, default=0)
    AlarmEcho: Mapped[bool] = mapped_column('AlarmEcho', nullable=True, default=False)
    RemotePC: Mapped[bool] = mapped_column('RemotePC', nullable=True, default=False)
    ModemAlarm: Mapped[int] = mapped_column('ModemAlarm', nullable=True, default=0)
    SaveLastDev: Mapped[bool] = mapped_column('SaveLastDev', nullable=True, default=True)
    TimeZone: Mapped[str] = mapped_column('TimeZone', default='')
    DST: Mapped[bool] = mapped_column('DST', nullable=True)
    AlarmEmail: Mapped[int] = mapped_column('AlarmEmail', nullable=True, default=0)
    EKey: Mapped[str] = mapped_column('EKey', default='')


class AclGrp(AcsDataBase):
    __tablename__ = 'AclGrp'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    AclGrpNameID: Mapped[int] = mapped_column('AclGrpNameID', ForeignKey('AclGrpName.ID'), primary_key=True, default=0)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True, default=1)
    Dev: Mapped[int] = mapped_column('Dev', primary_key=True, default=1)
    Tz1: Mapped[int] = mapped_column('Tz1', default=1)
    Tz2: Mapped[int] = mapped_column('Tz2', default=1)
    Tz3: Mapped[int] = mapped_column('Tz3', default=1)
    Tz4: Mapped[int] = mapped_column('Tz4', default=1)


class AclName(AcsDataBase):
    __tablename__ = 'AclName'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True, default=1)
    Acl: Mapped[int] = mapped_column('Acl', primary_key=True, default=1)
    Name: Mapped[str] = mapped_column('Name')
    Notes: Mapped[str] = mapped_column('Notes', default='')
    Visitor: Mapped[bool] = mapped_column('Visitor', nullable=True)
    AclGrpComboID: Mapped[int] = mapped_column('AclGrpComboID', nullable=True, default=0)
    LastUse: Mapped[datetime] = mapped_column('LastUse', nullable=True, default=datetime.now())


class DEV(AcsDataBase):
    __tablename__ = 'DEV'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    Device: Mapped[int] = mapped_column('Device', primary_key=True, default=0)
    Name: Mapped[str] = mapped_column('Name')
    Type: Mapped[str] = mapped_column('Type', default='D5')
    OpenTime: Mapped[int] = mapped_column('OpenTime', nullable=True, default=5)
    TooLong: Mapped[int] = mapped_column('TooLong', nullable=True, default=60)
    TimedATPB: Mapped[int] = mapped_column('TimedATPB', nullable=True, default=0)
    Oll: Mapped[bool] = mapped_column('Oll', nullable=True, default=False)
    Lnk2Out1: Mapped[bool] = mapped_column('Lnk2Out1', nullable=True, default=False)
    ReverseData: Mapped[bool] = mapped_column('ReverseData', nullable=True, default=False)
    DoorInputs: Mapped[bool] = mapped_column('DoorInputs', nullable=True, default=True)
    DodRelock: Mapped[bool] = mapped_column('DodRelock', nullable=True, default=True)
    Trace: Mapped[bool] = mapped_column('Trace', nullable=True, default=False)
    ExitUnlock: Mapped[bool] = mapped_column('ExitUnlock', nullable=True, default=True)
    LogExitReq: Mapped[bool] = mapped_column('LogExitReq', nullable=True, default=False)
    DelayUnlock: Mapped[bool] = mapped_column('DelayUnlock', nullable=True, default=False)
    KpTz1: Mapped[int] = mapped_column('KpTz1', nullable=True, default=0)
    KpTz2: Mapped[int] = mapped_column('KpTz2', nullable=True, default=0)
    CrTz1: Mapped[int] = mapped_column('CrTz1', nullable=True, default=0)
    CrTz2: Mapped[int] = mapped_column('CrTz2', nullable=True, default=0)
    IrTz1: Mapped[int] = mapped_column('IrTz1', nullable=True, default=0)
    IrTz2: Mapped[int] = mapped_column('IrTz2', nullable=True, default=0)
    AntiPass1: Mapped[int] = mapped_column('AntiPass1', nullable=True, default=0)
    AntiPass2: Mapped[int] = mapped_column('AntiPass2', nullable=True, default=0)
    AntiPass3: Mapped[int] = mapped_column('AntiPass3', nullable=True, default=0)
    AntiPass4: Mapped[int] = mapped_column('AntiPass4', nullable=True, default=0)
    ActionMsg: Mapped[int] = mapped_column('ActionMsg', nullable=True, default=0)
    DeniedMsg: Mapped[int] = mapped_column('DeniedMsg', nullable=True, default=0)
    TNA: Mapped[str] = mapped_column('TNA', nullable=True, default='N')
    WireTag: Mapped[str] = mapped_column('WireTag', default='')
    DlFlag: Mapped[int] = mapped_column('DlFlag', nullable=True, default=0)
    Enabled: Mapped[bool] = mapped_column('Enabled', nullable=True, default=True)
    RAM: Mapped[int] = mapped_column('RAM', nullable=True, default=0)
    FwVersion: Mapped[int] = mapped_column('FwVersion', nullable=True, default=0)
    FwDate: Mapped[datetime] = mapped_column('FwDate', nullable=True)
    CpuType: Mapped[int] = mapped_column('CpuType', nullable=True, default=0)
    IoType: Mapped[int] = mapped_column('IoType', nullable=True, default=0)
    LowAC: Mapped[bool] = mapped_column('LowAC', nullable=True, default=False)
    HighAC: Mapped[bool] = mapped_column('HighAC', nullable=True, default=False)
    LowBattery: Mapped[bool] = mapped_column('LowBattery', nullable=True, default=False)
    Notes: Mapped[str] = mapped_column('Notes', default='')
    AlarmEcho: Mapped[bool] = mapped_column('AlarmEcho', nullable=True, default=False)
    CkSum: Mapped[int] = mapped_column('CkSum', nullable=True, default=0)
    DisAbleCode: Mapped[bool] = mapped_column('DisAbleCode', nullable=True, default=False)
    AlarmEmail: Mapped[int] = mapped_column('AlarmEmail', nullable=True, default=0)


class DGRP(AcsDataBase):
    __tablename__ = 'DGRP'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True, default=0)
    DGrp: Mapped[int] = mapped_column('DGrp', primary_key=True, default=0)
    DlFlag: Mapped[int] = mapped_column('DlFlag', nullable=True, default=0)
    D0: Mapped[bool] = mapped_column('D0', nullable=True)
    D1: Mapped[bool] = mapped_column('D1', nullable=True)
    D2: Mapped[bool] = mapped_column('D2', nullable=True)
    D3: Mapped[bool] = mapped_column('D3', nullable=True)
    D4: Mapped[bool] = mapped_column('D4', nullable=True)
    D5: Mapped[bool] = mapped_column('D5', nullable=True)
    D6: Mapped[bool] = mapped_column('D6', nullable=True)
    D7: Mapped[bool] = mapped_column('D7', nullable=True)
    D8: Mapped[bool] = mapped_column('D8', nullable=True)
    D9: Mapped[bool] = mapped_column('D9', nullable=True)
    D10: Mapped[bool] = mapped_column('D10', nullable=True)
    D11: Mapped[bool] = mapped_column('D11', nullable=True)
    D12: Mapped[bool] = mapped_column('D12', nullable=True)
    D13: Mapped[bool] = mapped_column('D13', nullable=True)
    D14: Mapped[bool] = mapped_column('D14', nullable=True)
    D15: Mapped[bool] = mapped_column('D15', nullable=True)
    D16: Mapped[bool] = mapped_column('D16', nullable=True)
    D17: Mapped[bool] = mapped_column('D17', nullable=True)
    D18: Mapped[bool] = mapped_column('D18', nullable=True)
    D19: Mapped[bool] = mapped_column('D19', nullable=True)
    D20: Mapped[bool] = mapped_column('D20', nullable=True)
    D21: Mapped[bool] = mapped_column('D21', nullable=True)
    D22: Mapped[bool] = mapped_column('D22', nullable=True)
    D23: Mapped[bool] = mapped_column('D23', nullable=True)
    D24: Mapped[bool] = mapped_column('D24', nullable=True)
    D25: Mapped[bool] = mapped_column('D25', nullable=True)
    D26: Mapped[bool] = mapped_column('D26', nullable=True)
    D27: Mapped[bool] = mapped_column('D27', nullable=True)
    D28: Mapped[bool] = mapped_column('D28', nullable=True)
    D29: Mapped[bool] = mapped_column('D29', nullable=True)
    D30: Mapped[bool] = mapped_column('D30', nullable=True)
    D31: Mapped[bool] = mapped_column('D31', nullable=True)
    D32: Mapped[bool] = mapped_column('D32', nullable=True)
    D33: Mapped[bool] = mapped_column('D33', nullable=True)
    D34: Mapped[bool] = mapped_column('D34', nullable=True)
    D35: Mapped[bool] = mapped_column('D35', nullable=True)
    D36: Mapped[bool] = mapped_column('D36', nullable=True)
    D37: Mapped[bool] = mapped_column('D37', nullable=True)
    D38: Mapped[bool] = mapped_column('D38', nullable=True)
    D39: Mapped[bool] = mapped_column('D39', nullable=True)
    D40: Mapped[bool] = mapped_column('D40', nullable=True)
    D41: Mapped[bool] = mapped_column('D41', nullable=True)
    D42: Mapped[bool] = mapped_column('D42', nullable=True)
    D43: Mapped[bool] = mapped_column('D43', nullable=True)
    D44: Mapped[bool] = mapped_column('D44', nullable=True)
    D45: Mapped[bool] = mapped_column('D45', nullable=True)
    D46: Mapped[bool] = mapped_column('D46', nullable=True)
    D47: Mapped[bool] = mapped_column('D47', nullable=True)
    D48: Mapped[bool] = mapped_column('D48', nullable=True)
    D49: Mapped[bool] = mapped_column('D49', nullable=True)
    D50: Mapped[bool] = mapped_column('D50', nullable=True)
    D51: Mapped[bool] = mapped_column('D51', nullable=True)
    D52: Mapped[bool] = mapped_column('D52', nullable=True)
    D53: Mapped[bool] = mapped_column('D53', nullable=True)
    D54: Mapped[bool] = mapped_column('D54', nullable=True)
    D55: Mapped[bool] = mapped_column('D55', nullable=True)
    D56: Mapped[bool] = mapped_column('D56', nullable=True)
    D57: Mapped[bool] = mapped_column('D57', nullable=True)
    D58: Mapped[bool] = mapped_column('D58', nullable=True)
    D59: Mapped[bool] = mapped_column('D59', nullable=True)
    D60: Mapped[bool] = mapped_column('D60', nullable=True)
    D61: Mapped[bool] = mapped_column('D61', nullable=True)
    D62: Mapped[bool] = mapped_column('D62', nullable=True)
    D63: Mapped[bool] = mapped_column('D63', nullable=True)
    D64: Mapped[bool] = mapped_column('D64', nullable=True)
    D65: Mapped[bool] = mapped_column('D65', nullable=True)
    D66: Mapped[bool] = mapped_column('D66', nullable=True)
    D67: Mapped[bool] = mapped_column('D67', nullable=True)
    D68: Mapped[bool] = mapped_column('D68', nullable=True)
    D69: Mapped[bool] = mapped_column('D69', nullable=True)
    D70: Mapped[bool] = mapped_column('D70', nullable=True)
    D71: Mapped[bool] = mapped_column('D71', nullable=True)
    D72: Mapped[bool] = mapped_column('D72', nullable=True)
    D73: Mapped[bool] = mapped_column('D73', nullable=True)
    D74: Mapped[bool] = mapped_column('D74', nullable=True)
    D75: Mapped[bool] = mapped_column('D75', nullable=True)
    D76: Mapped[bool] = mapped_column('D76', nullable=True)
    D77: Mapped[bool] = mapped_column('D77', nullable=True)
    D78: Mapped[bool] = mapped_column('D78', nullable=True)
    D79: Mapped[bool] = mapped_column('D79', nullable=True)
    D80: Mapped[bool] = mapped_column('D80', nullable=True)
    D81: Mapped[bool] = mapped_column('D81', nullable=True)
    D82: Mapped[bool] = mapped_column('D82', nullable=True)
    D83: Mapped[bool] = mapped_column('D83', nullable=True)
    D84: Mapped[bool] = mapped_column('D84', nullable=True)
    D85: Mapped[bool] = mapped_column('D85', nullable=True)
    D86: Mapped[bool] = mapped_column('D86', nullable=True)
    D87: Mapped[bool] = mapped_column('D87', nullable=True)
    D88: Mapped[bool] = mapped_column('D88', nullable=True)
    D89: Mapped[bool] = mapped_column('D89', nullable=True)
    D90: Mapped[bool] = mapped_column('D90', nullable=True)
    D91: Mapped[bool] = mapped_column('D91', nullable=True)
    D92: Mapped[bool] = mapped_column('D92', nullable=True)
    D93: Mapped[bool] = mapped_column('D93', nullable=True)
    D94: Mapped[bool] = mapped_column('D94', nullable=True)
    D95: Mapped[bool] = mapped_column('D95', nullable=True)
    D96: Mapped[bool] = mapped_column('D96', nullable=True)
    D97: Mapped[bool] = mapped_column('D97', nullable=True)
    D98: Mapped[bool] = mapped_column('D98', nullable=True)
    D99: Mapped[bool] = mapped_column('D99', nullable=True)
    D100: Mapped[bool] = mapped_column('D100', nullable=True)
    D101: Mapped[bool] = mapped_column('D101', nullable=True)
    D102: Mapped[bool] = mapped_column('D102', nullable=True)
    D103: Mapped[bool] = mapped_column('D103', nullable=True)
    D104: Mapped[bool] = mapped_column('D104', nullable=True)
    D105: Mapped[bool] = mapped_column('D105', nullable=True)
    D106: Mapped[bool] = mapped_column('D106', nullable=True)
    D107: Mapped[bool] = mapped_column('D107', nullable=True)
    D108: Mapped[bool] = mapped_column('D108', nullable=True)
    D109: Mapped[bool] = mapped_column('D109', nullable=True)
    D110: Mapped[bool] = mapped_column('D110', nullable=True)
    D111: Mapped[bool] = mapped_column('D111', nullable=True)
    D112: Mapped[bool] = mapped_column('D112', nullable=True)
    D113: Mapped[bool] = mapped_column('D113', nullable=True)
    D114: Mapped[bool] = mapped_column('D114', nullable=True)
    D115: Mapped[bool] = mapped_column('D115', nullable=True)
    D116: Mapped[bool] = mapped_column('D116', nullable=True)
    D117: Mapped[bool] = mapped_column('D117', nullable=True)
    D118: Mapped[bool] = mapped_column('D118', nullable=True)
    D119: Mapped[bool] = mapped_column('D119', nullable=True)
    D120: Mapped[bool] = mapped_column('D120', nullable=True)
    D121: Mapped[bool] = mapped_column('D121', nullable=True)
    D122: Mapped[bool] = mapped_column('D122', nullable=True)
    D123: Mapped[bool] = mapped_column('D123', nullable=True)
    D124: Mapped[bool] = mapped_column('D124', nullable=True)
    D125: Mapped[bool] = mapped_column('D125', nullable=True)
    D126: Mapped[bool] = mapped_column('D126', nullable=True)
    D127: Mapped[bool] = mapped_column('D127', nullable=True)
    CkSum: Mapped[int] = mapped_column('CkSum', nullable=True, default=0)


class FACIL(AcsDataBase):
    __tablename__ = 'FACIL'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    Facility: Mapped[int] = mapped_column('Facility', primary_key=True)
    Device: Mapped[int] = mapped_column('Device', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    DlFlag: Mapped[int] = mapped_column('DlFlag', nullable=True, default=0)
    Notes: Mapped[str] = mapped_column('Notes', default='')
    CkSum: Mapped[int] = mapped_column('CkSum', nullable=True, default=0)


class HOL(AcsDataBase):
    __tablename__ = 'HOL'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    HolDate: Mapped[datetime] = mapped_column('HolDate', primary_key=True, default=datetime.now())
    Type: Mapped[int] = mapped_column('Type', default=1)
    Name: Mapped[str] = mapped_column('Name')
    DlFlag: Mapped[int] = mapped_column('DlFlag', nullable=True, default=0)
    Notes: Mapped[str] = mapped_column('Notes', default='')
    CkSum: Mapped[int] = mapped_column('CkSum', nullable=True, default=0)
    ReOccurring: Mapped[bool] = mapped_column('ReOccurring', nullable=True)


class KeyName(AcsDataBase):
    __tablename__ = 'KeyName'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True, default=0)
    Name: Mapped[str] = mapped_column('Name', primary_key=True)
    Door: Mapped[str] = mapped_column('Door', nullable=True)
    KeyType: Mapped[str] = mapped_column('KeyType', nullable=True)
    Pinning: Mapped[str] = mapped_column('Pinning', nullable=True)
    Notes: Mapped[str] = mapped_column('Notes', default='')


class LocCards(AcsDataBase):
    __tablename__ = 'LocCards'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    CardID: Mapped[int] = mapped_column('CardID', ForeignKey('CARDS.ID'), primary_key=True, default=0)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True, default=1)
    Acl: Mapped[int] = mapped_column('Acl', nullable=True, default=0)
    Oll: Mapped[int] = mapped_column('Oll', nullable=True, default=0)
    LastDate: Mapped[datetime] = mapped_column('LastDate', nullable=True,
                                               default=datetime(year=1000, month=1, day=1, hour=0, minute=0, second=0))
    LastDev: Mapped[int] = mapped_column('LastDev', nullable=True, default=-1)
    InOut1: Mapped[str] = mapped_column('InOut1', nullable=True, default='N')
    InOut2: Mapped[str] = mapped_column('InOut2', nullable=True, default='N')
    InOut3: Mapped[str] = mapped_column('InOut3', nullable=True, default='N')
    InOut4: Mapped[str] = mapped_column('InOut4', nullable=True, default='N')
    DlFlag: Mapped[int] = mapped_column('DlFlag', nullable=True, default=0)
    CkSum: Mapped[int] = mapped_column('CkSum', nullable=True, default=0)
    Acl1: Mapped[int] = mapped_column('Acl1', nullable=True, default=-1)
    Acl2: Mapped[int] = mapped_column('Acl2', nullable=True, default=-1)
    Acl3: Mapped[int] = mapped_column('Acl3', nullable=True, default=-1)
    Acl4: Mapped[int] = mapped_column('Acl4', nullable=True, default=-1)


class LocMem(AcsDataBase):
    __tablename__ = 'LocMem'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True, default=0)
    TableNum: Mapped[int] = mapped_column('TableNum', primary_key=True, default=0)
    Name: Mapped[str] = mapped_column('Name')
    NumRecs: Mapped[int] = mapped_column('NumRecs', nullable=True, default=0)
    MaxRecs: Mapped[int] = mapped_column('MaxRecs', nullable=True, default=0)
    BytesEach: Mapped[int] = mapped_column('BytesEach', nullable=True, default=0)
    TotalBytes: Mapped[int] = mapped_column('TotalBytes', nullable=True, default=0)


class MSG(AcsDataBase):
    __tablename__ = 'MSG'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), primary_key=True)
    Name: Mapped[str] = mapped_column('Name', primary_key=True)
    Msg: Mapped[str] = mapped_column('Msg')


class MapName(AcsDataBase):
    __tablename__ = 'MapName'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), nullable=True)
    Name: Mapped[str] = mapped_column('Name')
    FileName: Mapped[str] = mapped_column('FileName')
    Icon: Mapped[int] = mapped_column('Icon', nullable=True, default=0)
    DispOrder: Mapped[int] = mapped_column('DispOrder', nullable=True, default=0)
    Notes: Mapped[str] = mapped_column('Notes', default='')
    Height: Mapped[int] = mapped_column('Height', nullable=True, default=0)
    Width: Mapped[int] = mapped_column('Width', nullable=True, default=0)


class MapPoint(AcsDataBase):
    __tablename__ = 'MapPoint'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    MapID: Mapped[int] = mapped_column('MapID', ForeignKey('MapName.ID'))
    PointID: Mapped[int] = mapped_column('PointID', nullable=True, default=0)
    PointType: Mapped[int] = mapped_column('PointType', nullable=True, default=0)
    XPos: Mapped[int] = mapped_column('XPos', default=0)
    YPos: Mapped[int] = mapped_column('YPos', default=0)


class NAMES(AcsDataBase):
    __tablename__ = 'NAMES'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', nullable=True)
    LName: Mapped[str] = mapped_column('LName')
    FName: Mapped[str] = mapped_column('FName', nullable=True, default=' ')
    Company: Mapped[int] = mapped_column('Company', nullable=True, default=0)
    Visitor: Mapped[bool] = mapped_column('Visitor', nullable=True, default=False)
    Trace: Mapped[bool] = mapped_column('Trace', nullable=True, default=False)
    PrintIt: Mapped[bool] = mapped_column('PrintIt', nullable=True, default=False)
    Notes: Mapped[str] = mapped_column('Notes', default='')


class EmailGrp(AcsDataBase):
    __tablename__ = 'EmailGrp'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    EmailGrpNameID: Mapped[int] = mapped_column('EmailGrpNameID', ForeignKey('EmailGrpName.ID'))
    NameID: Mapped[int] = mapped_column('NameID', ForeignKey('NAMES.ID'), nullable=True, default=0)
    TZ: Mapped[int] = mapped_column('TZ', nullable=True, default=0)


class Images(AcsDataBase):
    __tablename__ = 'Images'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    NameID: Mapped[int] = mapped_column('NameID', ForeignKey('NAMES.ID'), default=0)
    ImgType: Mapped[int] = mapped_column('ImgType', default=0)
    FileName: Mapped[str] = mapped_column('FileName', nullable=True)


class Keys(AcsDataBase):
    __tablename__ = 'Keys'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    KeyID: Mapped[int] = mapped_column('KeyID', ForeignKey('KeyName.ID'), default=0)
    NameID: Mapped[int] = mapped_column('NameID', ForeignKey('NAMES.ID'), default=0)
    Returned: Mapped[bool] = mapped_column('Returned', nullable=True)
    Issued: Mapped[datetime] = mapped_column('Issued')
    IssueNum: Mapped[int] = mapped_column('IssueNum', nullable=True, default=0)


class OGRP(AcsDataBase):
    __tablename__ = 'OGRP'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    Ogrp: Mapped[int] = mapped_column('Ogrp', primary_key=True)
    IO: Mapped[int] = mapped_column('IO', primary_key=True)
    IOType: Mapped[int] = mapped_column('IOType', primary_key=True, default=0)
    RespType: Mapped[int] = mapped_column('RespType', default=0)
    SetTime: Mapped[int] = mapped_column('SetTime', default=0)
    TimeType: Mapped[str] = mapped_column('TimeType')
    TZ: Mapped[int] = mapped_column('TZ', default=0)
    DlFlag: Mapped[int] = mapped_column('DlFlag', nullable=True, default=0)
    CkSum: Mapped[int] = mapped_column('CkSum', nullable=True, default=0)


class OLL(AcsDataBase):
    __tablename__ = 'OLL'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True, default=0)
    Oll: Mapped[int] = mapped_column('Oll', primary_key=True)
    Device: Mapped[int] = mapped_column('Device', primary_key=True)
    Ogrp: Mapped[int] = mapped_column('Ogrp', primary_key=True)
    DlFlag: Mapped[int] = mapped_column('DlFlag', nullable=True, default=0)
    CkSum: Mapped[int] = mapped_column('CkSum', nullable=True, default=0)


class OgrpName(AcsDataBase):
    __tablename__ = 'OgrpName'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    Ogrp: Mapped[int] = mapped_column('Ogrp', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    Notes: Mapped[str] = mapped_column('Notes', default='')


class OllName(AcsDataBase):
    __tablename__ = 'OllName'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    Oll: Mapped[int] = mapped_column('Oll', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    Notes: Mapped[str] = mapped_column('Notes', default='')
    Visitor: Mapped[bool] = mapped_column('Visitor', nullable=True)


class OprCom(AcsDataBase):
    __tablename__ = 'OprCom'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    Name: Mapped[str] = mapped_column('Name')
    Comment: Mapped[str] = mapped_column('Comment')
    DispOrder: Mapped[int] = mapped_column('DispOrder', default=1)


class OvrGrpName(AcsDataBase):
    __tablename__ = 'OvrGrpName'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', primary_key=True, default=0)
    Name: Mapped[str] = mapped_column('Name', primary_key=True)
    GrpType: Mapped[int] = mapped_column('GrpType', default=3)
    Icon1: Mapped[int] = mapped_column('Icon1', nullable=True, default=1)
    Icon2: Mapped[int] = mapped_column('Icon2', nullable=True, default=2)
    Notes: Mapped[str] = mapped_column('Notes', default='')
    DispOrder: Mapped[int] = mapped_column('DispOrder', nullable=True, default=0)


class OvrGrp(AcsDataBase):
    __tablename__ = 'OvrGrp'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    OvrGrpID: Mapped[int] = mapped_column('OvrGrpID', ForeignKey('OvrGrpName.ID'), default=0)
    PointID: Mapped[int] = mapped_column('PointID', default=0)


class OvrSchedule(AcsDataBase):
    __tablename__ = 'OvrSchedule'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    PointID: Mapped[int] = mapped_column('PointID', default=0)
    PointType: Mapped[int] = mapped_column('PointType', nullable=True, default=0)
    StartCmd: Mapped[int] = mapped_column('StartCmd', default=2)
    StartDate: Mapped[datetime] = mapped_column('StartDate')
    StopCmd: Mapped[int] = mapped_column('StopCmd', default=3)
    StopDate: Mapped[datetime] = mapped_column('StopDate')
    Opr: Mapped[str] = mapped_column('Opr')
    OprID: Mapped[int] = mapped_column('OprID', nullable=True, default=0)
    Status: Mapped[int] = mapped_column('Status', nullable=True, default=0)


class OvrSchedule2(AcsDataBase):
    __tablename__ = 'OvrSchedule2'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    PointID: Mapped[int] = mapped_column('PointID', default=0)
    PointType: Mapped[int] = mapped_column('PointType', nullable=True, default=0)
    StartCmd: Mapped[int] = mapped_column('StartCmd', default=2)
    StartDate: Mapped[datetime] = mapped_column('StartDate')
    StopCmd: Mapped[int] = mapped_column('StopCmd', default=3)
    StopDate: Mapped[datetime] = mapped_column('StopDate')
    Opr: Mapped[str] = mapped_column('Opr')
    OprID: Mapped[int] = mapped_column('OprID', nullable=True, default=0)
    Status: Mapped[int] = mapped_column('Status', nullable=True, default=0)


class PHONE(AcsDataBase):
    __tablename__ = 'PHONE'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    NameID: Mapped[int] = mapped_column('NameID', ForeignKey('NAMES.ID'))
    Name: Mapped[str] = mapped_column('Name')
    Phone: Mapped[str] = mapped_column('Phone')
    Notes: Mapped[str] = mapped_column('Notes', default='')


class SkillName(AcsDataBase):
    __tablename__ = 'SkillName'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), primary_key=True, default=0)
    Name: Mapped[str] = mapped_column('Name', primary_key=True)


class Skills(AcsDataBase):
    __tablename__ = 'Skills'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    SkillID: Mapped[int] = mapped_column('SkillID', ForeignKey('SkillName.ID'), default=0)
    NameID: Mapped[int] = mapped_column('NameID', ForeignKey('NAMES.ID'), default=0)


class TZ(AcsDataBase):
    __tablename__ = 'TZ'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    Loc: Mapped[int] = mapped_column('Loc', ForeignKey('LOC.Loc'), primary_key=True)
    TZ: Mapped[int] = mapped_column('TZ', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    LinkStatus: Mapped[int] = mapped_column('LinkStatus', nullable=True, default=0)
    SunStart: Mapped[int] = mapped_column('SunStart', nullable=True, default=0)
    SunStop: Mapped[int] = mapped_column('SunStop', nullable=True, default=0)
    MonStart: Mapped[int] = mapped_column('MonStart', nullable=True, default=0)
    MonStop: Mapped[int] = mapped_column('MonStop', nullable=True, default=0)
    TueStart: Mapped[int] = mapped_column('TueStart', nullable=True, default=0)
    TueStop: Mapped[int] = mapped_column('TueStop', nullable=True, default=0)
    WedStart: Mapped[int] = mapped_column('WedStart', nullable=True, default=0)
    WedStop: Mapped[int] = mapped_column('WedStop', nullable=True, default=0)
    ThuStart: Mapped[int] = mapped_column('ThuStart', nullable=True, default=0)
    ThuStop: Mapped[int] = mapped_column('ThuStop', nullable=True, default=0)
    FriStart: Mapped[int] = mapped_column('FriStart', nullable=True, default=0)
    FriStop: Mapped[int] = mapped_column('FriStop', nullable=True, default=0)
    SatStart: Mapped[int] = mapped_column('SatStart', nullable=True, default=0)
    SatStop: Mapped[int] = mapped_column('SatStop', nullable=True, default=0)
    Hol1Start: Mapped[int] = mapped_column('Hol1Start', nullable=True, default=0)
    Hol1Stop: Mapped[int] = mapped_column('Hol1Stop', nullable=True, default=0)
    Hol2Start: Mapped[int] = mapped_column('Hol2Start', nullable=True, default=0)
    Hol2Stop: Mapped[int] = mapped_column('Hol2Stop', nullable=True, default=0)
    Hol3Start: Mapped[int] = mapped_column('Hol3Start', nullable=True, default=0)
    Hol3Stop: Mapped[int] = mapped_column('Hol3Stop', nullable=True, default=0)
    DlFlag: Mapped[int] = mapped_column('DlFlag', nullable=True, default=0)
    Notes: Mapped[str] = mapped_column('Notes', default='')
    CkSum: Mapped[int] = mapped_column('CkSum', nullable=True, default=0)


class UdfName(AcsDataBase):
    __tablename__ = 'UdfName'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', ForeignKey('LocGrp.LocGrp'), primary_key=True)
    UdfNum: Mapped[int] = mapped_column('UdfNum', primary_key=True)
    Name: Mapped[str] = mapped_column('Name')
    Required: Mapped[bool] = mapped_column('Required', nullable=True, default=False)
    Uniq: Mapped[bool] = mapped_column('Uniq', nullable=True, default=False)
    Mask: Mapped[str] = mapped_column('Mask', default='')
    StopDate: Mapped[bool] = mapped_column('StopDate', nullable=True)
    VisitorID: Mapped[bool] = mapped_column('VisitorID', nullable=True)
    CardNum: Mapped[bool] = mapped_column('CardNum', nullable=True)
    Hidden: Mapped[bool] = mapped_column('Hidden', nullable=True)
    Combo: Mapped[bool] = mapped_column('Combo', nullable=True)
    ComboOnly: Mapped[bool] = mapped_column('ComboOnly', nullable=True)
    Email: Mapped[bool] = mapped_column('Email', nullable=True, default=False)


class UDF(AcsDataBase):
    __tablename__ = 'UDF'

    ID: Mapped[int] = mapped_column('ID', nullable=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp', default=0)
    NameID: Mapped[int] = mapped_column('NameID', ForeignKey('NAMES.ID'), primary_key=True)
    UdfNum: Mapped[int] = mapped_column('UdfNum', primary_key=True)
    UdfText: Mapped[str] = mapped_column('UdfText', nullable=True, default='')


class UdfSel(AcsDataBase):
    __tablename__ = 'UdfSel'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    LocGrp: Mapped[int] = mapped_column('LocGrp')
    UdfNum: Mapped[int] = mapped_column('UdfNum')
    ListOrder: Mapped[int] = mapped_column('ListOrder', nullable=True, default=0)
    SelText: Mapped[str] = mapped_column('SelText')


class Wav(AcsDataBase):
    __tablename__ = 'Wav'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    FileName: Mapped[str] = mapped_column('FileName')


class WorkStations(AcsDataBase):
    __tablename__ = 'WorkStations'

    ID: Mapped[int] = mapped_column('ID', primary_key=True, nullable=True)
    WorkSta: Mapped[int] = mapped_column('WorkSta', nullable=True, default=0)
    Name: Mapped[str] = mapped_column('Name', nullable=True)
    LastUsed: Mapped[datetime] = mapped_column('LastUsed', nullable=True)


class LogDataBase(DeclarativeBase):
    pass


class EvnLog(LogDataBase):
    __tablename__ = 'EvnLog'

    """
    If the columns designated as primary keys seems weird, that's because it definitely is super weird. There is not a
    specified primary key on the table and no set of columns that uniquely identifies a row. We had duplicates across
    the entire table. The columns with primary key set were the ones that didn't increase the number of duplicates we
    had. e.g. the number of rows grouped on those columns should equal the number of distinct rows across all columns.
    """
    TimeDate: Mapped[datetime] = mapped_column('TimeDate', primary_key=True)
    Loc: Mapped[int] = mapped_column('Loc', default=0)
    Event: Mapped[int] = mapped_column('Event', default=0, primary_key=True)
    Dev: Mapped[int] = mapped_column('Dev', default=-1)
    IO: Mapped[int] = mapped_column('IO', default=0)
    IOName: Mapped[str] = mapped_column('IOName', default='', primary_key=True)
    Code: Mapped[float] = mapped_column('Code', default=0.0, primary_key=True)
    LName: Mapped[str] = mapped_column('LName', default='')
    FName: Mapped[str] = mapped_column('FName', default='')
    Opr: Mapped[str] = mapped_column('Opr', default='')
    Ws: Mapped[str] = mapped_column('Ws', default='')
